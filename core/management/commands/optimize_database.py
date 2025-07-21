"""
Django management command for database optimization.

This command analyzes database performance, creates indexes,
and provides optimization recommendations.
"""

from django.core.management.base import BaseCommand, CommandError

from core.database_optimization import (
    database_monitor,
    database_optimizer,
    query_optimizer,
)


class Command(BaseCommand):
    help = "Optimize database performance with indexes and analysis"

    def add_arguments(self, parser):
        parser.add_argument(
            "--analyze-only",
            action="store_true",
            help="Only analyze performance, do not create indexes",
        )
        parser.add_argument(
            "--create-indexes",
            action="store_true",
            help="Create recommended database indexes",
        )
        parser.add_argument(
            "--check-slow-queries",
            action="store_true",
            help="Analyze slow queries and provide recommendations",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=100.0,
            help="Slow query threshold in milliseconds (default: 100ms)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting database optimization..."))

        if options["analyze_only"]:
            self.analyze_database()
        elif options["create_indexes"]:
            self.create_indexes()
        elif options["check_slow_queries"]:
            self.analyze_slow_queries(options["threshold"])
        else:
            # Run full optimization
            self.analyze_database()
            self.create_indexes()
            self.analyze_slow_queries(options["threshold"])

        self.stdout.write(self.style.SUCCESS("Database optimization completed!"))

    def analyze_database(self):
        """Analyze database performance and statistics."""
        self.stdout.write("Analyzing database performance...")

        # Get database statistics
        stats = database_monitor.get_database_stats()

        # Display connection info
        conn_info = stats["connection_info"]
        self.stdout.write(f"Database Connections:")
        self.stdout.write(f"  Total: {conn_info.get('total_connections', 'unknown')}")
        self.stdout.write(f"  Active: {conn_info.get('active_connections', 'unknown')}")
        self.stdout.write(f"  Idle: {conn_info.get('idle_connections', 'unknown')}")

        # Display table statistics
        table_stats = stats["table_stats"]
        if table_stats:
            self.stdout.write("\nTable Statistics:")
            for table_name, table_info in list(table_stats.items())[
                :10
            ]:  # Top 10 tables
                self.stdout.write(
                    f"  {table_name}: {table_info['live_rows']} rows, "
                    f"{table_info['dead_rows']} dead rows"
                )

        # Display query performance
        query_perf = stats["query_performance"]
        if query_perf["total_queries"] > 0:
            self.stdout.write(f"\nQuery Performance:")
            self.stdout.write(f"  Total queries: {query_perf['total_queries']}")
            self.stdout.write(f"  Average time: {query_perf['avg_query_time']:.3f}s")
            self.stdout.write(f"  Max time: {query_perf['max_query_time']:.3f}s")

        # Check for missing indexes
        self.stdout.write("\nChecking for missing indexes...")
        missing_indexes = database_optimizer.check_missing_indexes()

        for model_name, recommendations in missing_indexes.items():
            if recommendations:
                self.stdout.write(f"\n{model_name}:")
                for rec in recommendations:
                    self.stdout.write(f"  - {rec['reason']}")
                    self.stdout.write(f"    SQL: {rec['index_sql']}")

    def create_indexes(self):
        """Create recommended database indexes."""
        self.stdout.write("Creating database indexes...")

        try:
            query_optimizer.create_database_indexes()
            self.stdout.write(
                self.style.SUCCESS("Database indexes created successfully!")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating indexes: {str(e)}"))
            raise CommandError(f"Index creation failed: {str(e)}")

    def analyze_slow_queries(self, threshold_ms):
        """Analyze slow queries and provide recommendations."""
        self.stdout.write(f"Analyzing slow queries (threshold: {threshold_ms}ms)...")

        # Enable query logging if not already enabled
        from django.conf import settings

        if not getattr(settings, "LOGGING_CAPTURE_SQL", False):
            self.stdout.write(
                self.style.WARNING(
                    "Query logging is not enabled. "
                    "Set LOGGING_CAPTURE_SQL = True in settings to capture queries."
                )
            )
            return

        slow_queries = database_optimizer.analyze_slow_queries(threshold_ms)

        if not slow_queries:
            self.stdout.write("No slow queries found.")
            return

        self.stdout.write(f"Found {len(slow_queries)} slow queries:")

        for i, analysis in enumerate(slow_queries, 1):
            self.stdout.write(f"\nSlow Query #{i}:")
            self.stdout.write(f"  Execution time: {analysis.execution_time:.2f}ms")
            self.stdout.write(f"  Query: {analysis.query[:100]}...")

            if analysis.recommendations:
                self.stdout.write("  Recommendations:")
                for rec in analysis.recommendations:
                    self.stdout.write(f"    - {rec}")
