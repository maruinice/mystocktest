import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_ai_trading.app.core.database import SessionLocal
from sqlalchemy import text

def check_models():
    db = SessionLocal()
    try:
        # 查询所有模型
        result = db.execute(text("SELECT * FROM ai_models"))
        models = result.fetchall()
        
        print(f"Found {len(models)} models:")
        for model in models:
            print(f"  - {model}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_models()
