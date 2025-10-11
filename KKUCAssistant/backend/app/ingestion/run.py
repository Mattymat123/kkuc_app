"""
CLI entry point for KKUC Ingestion Pipeline
Run with: python -m app.ingestion.run
"""
import sys
from .config import Config
from .pipeline import IngestionPipeline


def main():
    """Main entry point"""
    print("\n🔧 Initializing KKUC Ingestion Pipeline...\n")
    
    # Check for test mode flag
    if '--test' in sys.argv:
        Config.TEST_MODE = True
        print("⚠️  Running in TEST MODE (first 5 pages only)\n")
    
    try:
        # Initialize and run pipeline
        pipeline = IngestionPipeline(Config)
        pipeline.run()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
