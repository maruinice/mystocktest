#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速检查数据库中真实股票样本（排除模拟股票）
"""

from app.services.strategy_database_service import strategy_db_service


def main():
    print("🔎 随机抽取10只真实股票样本 (排除模拟股票)...")
    with strategy_db_service.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ts_code, symbol, name, market, industry
            FROM stock_basic
            WHERE list_status = 'L'
              AND sync_status = 'active'
              AND name NOT LIKE '模拟股票%'
            ORDER BY RAND()
            LIMIT 10
            """
        )
        rows = cursor.fetchall()
        for i, row in enumerate(rows, 1):
            print(f"  {i}. {row['ts_code']} | {row['name']} | {row['market']} | {row['industry']}")


if __name__ == "__main__":
    main()