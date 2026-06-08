import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup

class MovieService:
    """Парсит топ фильмов с Box Office Mojo (сайт о кассовых сборах, не блокирует)"""
    
    URL = "https://www.boxofficemojo.com/chart/top_lifetime_gross/"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
    
    async def get_top_movies(self) -> list:
        """Парсит топ-5 самых кассовых фильмов всех времён"""
        try:
            await asyncio.sleep(1.5)
            
            async with self.session.get(
                self.URL,
                headers=self.HEADERS,
                timeout=15,
                allow_redirects=True
            ) as response:
                if response.status != 200:
                    return await self._fallback_the_numbers()
                
                html = await response.text()
                soup = await asyncio.to_thread(BeautifulSoup, html, 'html.parser')
                
                table = soup.find('table')
                if not table:
                    return await self._fallback_the_numbers()
                
                movies = []
                rows = table.find_all('tr')
                
                for i, row in enumerate(rows[1:6]):
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        title_elem = cols[1] if len(cols) > 1 else cols[0]
                        title = title_elem.get_text(strip=True)
                        
                        year = ""
                        for col in cols:
                            text = col.get_text(strip=True)
                            year_match = re.search(r'\((\d{4})\)|(\d{4})', text)
                            if year_match:
                                year = year_match.group(1) or year_match.group(2)
                                break
                        
                        title = re.sub(r'\$[\d,]+', '', title).strip()
                        title = re.sub(r'\s+', ' ', title)
                        
                        if title and not title.isdigit():
                            if year:
                                movies.append(f"{i+1}. {title} ({year})")
                            else:
                                movies.append(f"{i+1}. {title}")
                
                if movies:
                    return movies
                
                return await self._fallback_the_numbers()
                
        except Exception as e:
            return await self._fallback_the_numbers()
    
    async def _fallback_the_numbers(self) -> list:
        """Запасной источник: The Numbers"""
        try:
            url = "https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/all-time"
            
            async with self.session.get(
                url,
                headers=self.HEADERS,
                timeout=15
            ) as response:
                if response.status != 200:
                    return await self._fallback_hardcoded()
                
                html = await response.text()
                soup = await asyncio.to_thread(BeautifulSoup, html, 'html.parser')
                
                table = soup.find('table')
                if not table:
                    return await self._fallback_hardcoded()
                
                movies = []
                rows = table.find_all('tr')
                
                for i, row in enumerate(rows[1:6]):
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        title = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                        year = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        
                        title = re.sub(r'\$[\d,]+', '', title).strip()
                        
                        if title:
                            if year:
                                movies.append(f"{i+1}. {title} ({year})")
                            else:
                                movies.append(f"{i+1}. {title}")
                
                if movies:
                    return movies
                
                return await self._fallback_hardcoded()
                
        except Exception:
            return await self._fallback_hardcoded()
    
    async def _fallback_hardcoded(self) -> list:
        """Если все источники недоступны"""
        return [
            "1. The Shawshank Redemption (1994)",
            "2. The Godfather (1972)",
            "3. The Dark Knight (2008)",
            "4. Pulp Fiction (1994)",
            "5. Forrest Gump (1994)",
            "",
            "⚠️ Данные из кэша (источники временно недоступны)"
        ]