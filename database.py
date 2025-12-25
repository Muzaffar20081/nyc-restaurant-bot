import json
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_order(self, user_id: int, order_data: dict) -> bool:
        """Сохранить заказ в базу"""
        try:
            filename = os.path.join(self.data_dir, f"orders_{user_id}.json")
            orders = self.load_orders(user_id)
            order_data["order_id"] = len(orders) + 1
            order_data["timestamp"] = datetime.now().isoformat()
            orders.append(order_data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения заказа: {e}")
            return False
    
    def load_orders(self, user_id: int) -> list:
        """Загрузить заказы пользователя"""
        try:
            filename = os.path.join(self.data_dir, f"orders_{user_id}.json")
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")
            return []
    
    def get_user_stats(self, user_id: int) -> dict:
        """Получить статистику пользователя"""
        orders = self.load_orders(user_id)
        total_orders = len(orders)
        total_spent = sum(order.get("total", 0) for order in orders)
        
        return {
            "total_orders": total_orders,
            "total_spent": total_spent,
            "last_order": orders[-1] if orders else None
        }

# Создаем глобальный экземпляр базы данных
db = Database()
