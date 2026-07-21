import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import Dict, List
import time
from dotenv import load_dotenv

load_dotenv()

class PokemonStockMonitor:
    """Monitor Pokemon TCG products across major retailers"""

    def __init__(self):
        # Discord webhook for notifications
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')

        # Track product prices to detect restocks
        self.stock_history: Dict[str, dict] = {}
        self.notified_products: set = set()

        # Search terms for Pokemon TCG products
        self.search_terms = [
            "Pokemon booster box",
            "Pokemon Scarlet Violet booster",
            "Pokemon 151",
            "Pokemon TCG ETB",
            "Pokemon sealed",
            "Pokemon bulk lot"
        ]

    def send_discord(self, message: str):
        """Send Discord notification"""
        try:
            payload = {
                "content": message
            }
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            if response.status_code == 204:
                print(f"✓ Discord notification sent: {message[:50]}...")
            else:
                print(f"✗ Discord error: {response.status_code}")
        except Exception as e:
            print(f"✗ Failed to send Discord message: {e}")

    def check_amazon(self) -> List[Dict]:
        """Monitor Amazon for Pokemon TCG products"""
        results = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for term in self.search_terms:
            try:
                # Amazon search
                url = f"amazon.com/s?k={term.replace(' ', '+')}"
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find products
                products = soup.find_all('div', {'data-component-type': 's-search-result'})[:3]

                for product in products:
                    try:
                        name = product.find('h2', {'class': 's-line-clamp-2'})
                        price = product.find('span', {'class': 'a-price-whole'})

                        if name:
                            product_name = name.get_text(strip=True)
                            product_price = price.get_text(strip=True) if price else "N/A"

                            results.append({
                                'retailer': 'Amazon',
                                'name': product_name,
                                'price': product_price,
                                'url': url,
                                'timestamp': datetime.now().isoformat()
                            })
                    except:
                        pass
            except Exception as e:
                print(f"Error checking Amazon: {e}")

        return results

    def check_walmart(self) -> List[Dict]:
        """Monitor Walmart for Pokemon TCG products"""
        results = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for term in self.search_terms:
            try:
                url = f"walmart.com/search?q={term.replace(' ', '+')}"
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                products = soup.find_all('div', {'class': 'mb0 ph0-xl pv0-xl'})[:3]

                for product in products:
                    try:
                        name = product.find('span', {'class': 'w-full'})
                        if name:
                            results.append({
                                'retailer': 'Walmart',
                                'name': name.get_text(strip=True),
                                'url': url,
                                'timestamp': datetime.now().isoformat()
                            })
                    except:
                        pass
            except Exception as e:
                print(f"Error checking Walmart: {e}")

        return results

    def check_target(self) -> List[Dict]:
        """Monitor Target for Pokemon TCG products"""
        results = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for term in self.search_terms:
            try:
                url = f"target.com/s?searchTerm={term.replace(' ', '+')}"
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                products = soup.find_all('div', {'class': 'h-full'})[:3]

                for product in products:
                    try:
                        name = product.find('span')
                        if name:
                            results.append({
                                'retailer': 'Target',
                                'name': name.get_text(strip=True),
                                'url': url,
                                'timestamp': datetime.now().isoformat()
                            })
                    except:
                        pass
            except Exception as e:
                print(f"Error checking Target: {e}")

        return results

    def check_bestbuy(self) -> List[Dict]:
        """Monitor Best Buy for Pokemon TCG products"""
        results = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for term in self.search_terms:
            try:
                url = f"bestbuy.com/site/searchpage.jsp?st={term.replace(' ', '+')}"
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                products = soup.find_all('div', {'class': 'sku-item'})[:3]

                for product in products:
                    try:
                        name = product.find('h4')
                        if name:
                            results.append({
                                'retailer': 'Best Buy',
                                'name': name.get_text(strip=True),
                                'url': url,
                                'timestamp': datetime.now().isoformat()
                            })
                    except:
                        pass
            except Exception as e:
                print(f"Error checking Best Buy: {e}")

        return results

    def check_all_retailers(self) -> List[Dict]:
        """Check all retailers for stock"""
        all_results = []

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking all retailers...")

        all_results.extend(self.check_amazon())
        all_results.extend(self.check_walmart())
        all_results.extend(self.check_target())
        all_results.extend(self.check_bestbuy())

        return all_results

    def process_results(self, results: List[Dict]):
        """Process results and send notifications for new stock"""
        for product in results:
            product_key = f"{product['retailer']}_{product['name']}"

            # Check if this is new or already notified
            if product_key not in self.stock_history:
                self.stock_history[product_key] = product

                # Send notification for new product
                message = f"🔔 **POKEMON RESTOCK!**\n\n**{product['retailer']}**\n{product['name']}\n\n🔗 Check: {product['url']}"
                self.send_discord(message)
                print(f"✓ Found: {product['retailer']} - {product['name'][:50]}")

    def run(self, interval: int = 300):
        """Run continuous monitoring"""
        print("🎮 Pokemon TCG Stock Monitor Started")
        print(f"Checking every {interval} seconds ({interval//60} minutes)")

        try:
            while True:
                results = self.check_all_retailers()
                self.process_results(results)

                print(f"Next check in {interval}s...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n❌ Monitor stopped")

if __name__ == "__main__":
    monitor = PokemonStockMonitor()
    monitor.run(interval=300)
