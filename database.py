# database.py - Простое хранилище в памяти
from datetime import datetime


class Database:
    def __init__(self):
        self.users = {}  # user_id: {cart: [], orders: []}
        self.orders = {}  # order_id: order_data
    
    def get_user(self, user_id):
        """Получить или создать пользователя"""
        if user_id not in self.users:
            self.users[user_id] = {
                "cart": [],
                "orders": [],
                "created_at": datetime.now()
            }
        return self.users[user_id]
    
    def add_to_cart(self, user_id, item):
        """Добавить товар в корзину"""
        user = self.get_user(user_id)
        user["cart"].append(item)
        return len(user["cart"])
    
    def get_cart(self, user_id):
        """Получить корзину пользователя"""
        user = self.get_user(user_id)
        return user["cart"]
    
    def clear_cart(self, user_id):
        """Очистить корзину"""
        user = self.get_user(user_id)
        count = len(user["cart"])
        user["cart"] = []
        return count
    
    def create_order(self, user_id, items, total):
        """Создать заказ"""
        user = self.get_user(user_id)
        order_id = f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        order = {
            "id": order_id,
            "user_id": user_id,
            "items": items.copy(),
            "total": total,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        user["orders"].append(order_id)
        self.orders[order_id] = order
        
        return order


# Глобальный экземпляр базы данных
db = Database()
