"""
CGV Movie Schedule Tracker - Lightweight Version for Home Assistant
Reads configuration from environment variables
"""
import os
import requests
import time
import hmac
import hashlib
import base64
import sys
from datetime import datetime
from urllib.parse import urlparse

# ============== CONFIGURATION FROM ENVIRONMENT ==============
# Read from Home Assistant add-on options (via environment variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TARGET_DATE = os.getenv("TARGET_DATE", "20251231")
MOVIE_NO = os.getenv("MOVIE_NO", "30000774")
SITE_NO = os.getenv("SITE_NO", "0013")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

# CGV API constants
CO_CD = "A420"
CGV_SECRET_KEY = "ydqXY0ocnFLmJGHr_zNzFcpjwAsXq_8JcBNURAkRscg"
# ============================================================


def generate_signature(pathname: str, timestamp: str, body: str = "") -> str:
    """
    Generate CGV API signature using HMAC-SHA256.
    
    Format from CGV JS:
    - t = timestamp (seconds since epoch)
    - e = pathname (URL path)
    - s = body (empty for GET requests)
    - signature = HmacSHA256("{timestamp}|{pathname}|{body}", secret_key).toBase64()
    """
    message = f"{timestamp}|{pathname}|{body}"
    
    signature = hmac.new(
        CGV_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')


class TelegramNotifier:
    """Handles Telegram notifications"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message via Telegram"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=30
            )
            response.raise_for_status()
            print(f"[Telegram] Message sent successfully")
            return True
        except Exception as e:
            print(f"[Telegram] Failed to send message: {e}")
            return False


class CGVScheduleTrackerLite:
    """Lightweight CGV schedule tracker using direct API calls"""
    
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        
        self.notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://cgv.co.kr",
            "Referer": "https://cgv.co.kr/",
        })
    
    def build_api_url(self, target_date: str) -> str:
        """Build the schedule API URL"""
        return (
            f"https://api.cgv.co.kr/cnm/atkt/searchSchByMov"
            f"?coCd={CO_CD}&siteNo={SITE_NO}&scnYmd={target_date}"
            f"&movNo={MOVIE_NO}&rtctlScopCd=08"
        )
    
    def check_schedule(self, target_date: str) -> dict:
        """Check schedule using direct API call with generated signature"""
        url = self.build_api_url(target_date)
        parsed = urlparse(url)
        
        # Get pathname only (NOT including query string - JS URL.pathname behavior)
        pathname = parsed.path
        
        # Generate timestamp and signature
        timestamp = str(int(time.time()))
        signature = generate_signature(pathname, timestamp, "")  # Empty body for GET
        
        headers = {
            "x-signature": signature,
            "x-timestamp": timestamp,
        }
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            
            print(f"[API] Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print(f"[API] Unauthorized - signature may be incorrect")
                return None
            else:
                print(f"[API] Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"[API] Request failed: {e}")
            return None
    
    def format_schedule_message(self, schedules: list, target_date: str) -> str:
        """Format the schedule data into a Telegram message"""
        date_obj = datetime.strptime(target_date, "%Y%m%d")
        date_str = date_obj.strftime("%Y-%m-%d")
        
        movie_name = schedules[0].get("movNm", "Unknown") if schedules else "Unknown"
        site_name = schedules[0].get("siteNm", "Unknown") if schedules else "Unknown"
        
        message = f"🎬 <b>CGV Schedule Open!</b>\n\n"
        message += f"📅 Date: {date_str}\n"
        message += f"🎥 Movie: {movie_name}\n"
        message += f"📍 Theater: {site_name}\n\n"
        
        # Group by screen type
        theaters = {}
        for sch in schedules:
            theater_name = sch.get("expoScnsNm", "Unknown")
            if theater_name not in theaters:
                theaters[theater_name] = []
            
            start_time = sch.get("scnsrtTm", "")
            if len(start_time) == 4:
                start_time = f"{start_time[:2]}:{start_time[2:]}"
            
            free_seats = sch.get("frSeatCnt", "?")
            total_seats = sch.get("stcnt", "?")
            
            theaters[theater_name].append({
                "time": start_time,
                "free": free_seats,
                "total": total_seats,
                "type": sch.get("movkndDsplNm", "")
            })
        
        for theater, times in theaters.items():
            message += f"🏢 <b>{theater}</b>\n"
            for t in times:
                message += f"  • {t['time']} ({t['type']}) - Seats: {t['free']}/{t['total']}\n"
            message += "\n"
        
        message += f"🔗 Book: https://cgv.co.kr/cnm/cgvChart/movieChart/{MOVIE_NO}"
        
        return message
    
    def run_once(self, target_date: str = None) -> bool:
        """Run a single check for the schedule"""
        if target_date is None:
            target_date = TARGET_DATE
        
        print(f"\n{'='*50}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CGV Check (Lite)")
        print(f"Date: {target_date}, Movie: {MOVIE_NO}, Theater: {SITE_NO}")
        print(f"{'='*50}\n")
        
        result = self.check_schedule(target_date)
        
        if result is None:
            print("[Error] Failed to get schedule data")
            return False
        
        schedules = result.get("data", [])
        status_code = result.get("statusCode")
        status_message = result.get("statusMessage", "")
        
        print(f"[Result] Status: {status_code}, Message: {status_message}")
        
        if schedules:
            print(f"\n🎉 Found {len(schedules)} schedules!")
            
            for sch in schedules[:5]:
                time_str = sch.get('scnsrtTm', '?')
                if len(time_str) == 4:
                    time_str = f"{time_str[:2]}:{time_str[2:]}"
                print(f"  - {time_str} @ {sch.get('expoScnsNm', '?')}")
            if len(schedules) > 5:
                print(f"  ... and {len(schedules) - 5} more")
            
            message = self.format_schedule_message(schedules, target_date)
            self.notifier.send_message(message)
            
            return True
        else:
            print(f"[Result] No schedules available yet")
            return False
    
    def run_continuous(self, target_date: str = None, interval: int = None):
        """Continuously monitor for schedule availability"""
        if target_date is None:
            target_date = TARGET_DATE
        if interval is None:
            interval = CHECK_INTERVAL
        
        print(f"Starting CGV monitor (Lite version - no browser)")
        print(f"Target: {target_date}, Interval: {interval}s")
        print(f"Press Ctrl+C to stop\n")
        
        while True:
            try:
                found = self.run_once(target_date)
                
                if found:
                    print("\n[OK] Schedule found! Stopping.")
                    break
                
                print(f"\n[Wait] Next check in {interval}s...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n[Stop] Stopped by user.")
                break
            except Exception as e:
                print(f"[Error] {e}")
                import traceback
                traceback.print_exc()
                time.sleep(interval)


def main():
    """Main entry point"""
    try:
        tracker = CGVScheduleTrackerLite()
        tracker.run_continuous(
            target_date=TARGET_DATE,
            interval=CHECK_INTERVAL
        )
    except ValueError as e:
        print(f"[Error] Configuration error: {e}")
        print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        sys.exit(1)
    except Exception as e:
        print(f"[Error] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

