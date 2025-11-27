import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_ai_trading.app.core.database import SessionLocal
from sqlalchemy import text

def delete_test_models():
    db = SessionLocal()
    try:
        # 检查表是否存在
        result = db.execute(text("SHOW TABLES LIKE 'ai_models'"))
        if not result.fetchone():
            print("Table 'ai_models' does not exist.")
            return

        # 删除指定模型
        models_to_delete = ['claude3_opus_001', 'gpt4_turbo_001']
        for model_id in models_to_delete:
            # 假设表名为 ai_models，主键为 model_id
            # 先检查是否存在
            check_sql = text(f"SELECT * FROM ai_models WHERE model_id = :model_id")
            exists = db.execute(check_sql, {"model_id": model_id}).fetchone()
            
            if exists:
                delete_sql = text(f"DELETE FROM ai_models WHERE model_id = :model_id")
                db.execute(delete_sql, {"model_id": model_id})
                print(f"Deleted model: {model_id}")
            else:
                print(f"Model not found: {model_id}")
        
        db.commit()
        print("Deletion process completed.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_test_models()
