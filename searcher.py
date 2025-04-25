import threading
import time
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# queries de busqueda
queries = [
    "donate page", "make a donation", "secure donation", "donate credit card",
    "donation form", "fundraiser donation", "ngo donate", "help children donate",
    "support our mission", "charity donation", "give now", "donate stripe", "donate paypal",
    "contribute to cause", "sponsor a child", "crowdfunding donation", "emergency donation",
    "donar con tarjeta", "donar ahora", "donación segura", "apoya nuestra causa",
    "haz una donación", "formulario de donación", "donar a ong", "donar stripe", "donar paypal",
    "buy now", "checkout", "online checkout", "payment form", "product checkout", "order summary",
    "add to cart", "buy product online", "buy with stripe", "comprar con tarjeta", "comprar ahora",
    "carrito de compras", "tienda en línea", "pago online", "checkout con stripe",
    "página de pago", "pago con paypal", "formulario de compra", "add payment method",
    "añadir metodo de pago", "add credit card", "añadir tarjeta", "tarjeta de crédito",
    "shopify checkout", "event ticket purchase", "get tickets", "sellfy payment", "sellix donate"
]

# plataformas de pago
plataformas_pago = [
    'stripe.com', 'paypal.com', 'braintreepayments.com', 'square.com',
    '2checkout.com', 'adyen.com', 'klarna.com', 'worldpay.com',
    'payoneer.com', 'moneris.com', 'payza.com', 'checkout.com', 'mercadopago.com'
]

# palabras clave en inputs de pago
input_keywords = [
    'card', 'credit', 'cvc', 'cvv', 'exp', 'number', 'payment', 'donate', 'amount', 'MM', 'AA', 'YY'
]

# Headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

sitios_live = []
urls_analizadas = set()
lock = threading.Lock()

# buscar URLs en DuckDuckGo
def buscar_urls(query, max_results=200):
    urls = set()
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            url = r['href']
            if url.startswith('http'):
                urls.add(url)
    return list(urls)

# analiza si una página tiene inputs relevantes y plataformas de pago
def analizar_url(url):
    with lock:
        if url in urls_analizadas:
            return
        urls_analizadas.add(url)

    try:
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        inputs = soup.find_all('input')
        if not inputs:
            return

        relevantes = 0
        for inp in inputs:
            name = (inp.get('name', '') + inp.get('id', '') + inp.get('placeholder', '')).lower()
            if any(kw in name for kw in input_keywords):
                relevantes += 1

        if relevantes >= 3:
            plataformas_encontradas = set()

            for tag in soup.find_all(['script', 'iframe', 'form', 'a']):
                for attr in ['src', 'href', 'action']:
                    val = tag.get(attr, '')
                    for plataforma in plataformas_pago:
                        if plataforma in val:
                            plataformas_encontradas.add(plataforma)

            html_str = str(soup).lower()
            for plataforma in plataformas_pago:
                if plataforma in html_str:
                    plataformas_encontradas.add(plataforma)

            with lock:
                print(f"\033[1;32m[LIVE] {url} | Inputs: {relevantes} | Plataformas: {list(plataformas_encontradas)}\033[0m")
                sitios_live.append(url)
        else:
            print(f"[SKIP] {url} | Inputs detectados: {relevantes}")

    except Exception as e:
        print(f"[ERROR] {url} => {e}")

# ejecutar la búsqueda
def ejecutar_masivo():
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            for query in queries:
                urls = buscar_urls(query, max_results=200)
                for url in urls:
                    executor.submit(analizar_url, url)
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Interrumpido por el usuario.")

    finally:
        print("\n\n📌 Sitios LIVE:")
        for sitio in sitios_live:
            print(f" - {sitio}")

if __name__ == "__main__":
    ejecutar_masivo()
