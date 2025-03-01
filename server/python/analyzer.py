import sys
import json
import asyncio
import traceback
from datetime import datetime

def log_debug(message):
    """Log debug messages to stderr"""
    print(f"DEBUG: {message}", file=sys.stderr)

def log_error(message):
    """Log error messages to stderr"""
    print(f"ERROR: {message}", file=sys.stderr)

async def main():
    try:
        log_debug("Starting analyzer.py")
        
        if len(sys.argv) < 2:
            raise ValueError("Token address required")

        token_address = sys.argv[1]
        chain = sys.argv[2] if len(sys.argv) > 2 else "ethereum"
        
        log_debug(f"Processing token: {token_address} on chain: {chain}")
        
        from crypto_analyzer import CryptoAnalyzer
        analyzer = CryptoAnalyzer(token_address, chain)
        
        log_debug("Running analysis...")
        results = await analyzer.run_analysis()
        log_debug("Analysis completed successfully")
        
        # Formater la sortie JSON avec une précision maximale
        formatted_results = {
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Imprimer le JSON sur stdout sans logs supplémentaires
        print(json.dumps(formatted_results))
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_data))
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        error_data = {
            "success": False,
            "error": f"Fatal error in main loop: {str(e)}",
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_data))
        sys.exit(1)