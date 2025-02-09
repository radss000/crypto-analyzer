import sys
import json
import asyncio
import traceback
from datetime import datetime
from crypto_analyzer import CryptoAnalyzer

async def main():
    try:
        if len(sys.argv) < 2:
            raise ValueError("Token address required")

        token_address = sys.argv[1]
        chain = sys.argv[2] if len(sys.argv) > 2 else "ethereum"
        
        print(f"Starting analysis for token: {token_address} on chain: {chain}", file=sys.stderr)
        
        analyzer = CryptoAnalyzer(token_address, chain)
        results = await analyzer.run_analysis()
        
        # Print the result to stdout for the Node.js server
        print(json.dumps(results))
        
    except Exception as e:
        error_msg = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_msg), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        error_msg = {
            "error": f"Fatal error in main loop: {str(e)}",
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_msg), file=sys.stderr)
        sys.exit(1)