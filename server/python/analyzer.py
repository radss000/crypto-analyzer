import sys
import json
import asyncio
from datetime import datetime
from crypto_analyzer import CryptoAnalyzer

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Token address required"}))
        sys.exit(1)

    token_address = sys.argv[1]
    chain = sys.argv[2] if len(sys.argv) > 2 else 'ethereum'  # Chaîne par défaut

    try:
        analyzer = CryptoAnalyzer(token_address, chain)
        results = await analyzer.run_analysis()
        print(json.dumps(results))
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())