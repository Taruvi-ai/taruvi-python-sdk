"""
Test cases for aggregation functionality in Taruvi Python SDK.

Tests cover:
- Simple aggregates (count, sum, avg, min, max)
- Multiple aggregates
- GROUP BY with single and multiple fields
- HAVING clause
- Combined filters with aggregations
- Response structure validation
"""

import pytest
from unittest.mock import Mock, patch
from taruvi._sync.modules.database import QueryBuilder, DatabaseModule


class TestAggregationQueryBuilder:
    """Test QueryBuilder aggregation methods."""

    def setup_method(self):
        """Setup mock client for each test."""
        self.mock_client = Mock()
        self.mock_client._http_client = Mock()
        self.mock_client._config = Mock()
        self.mock_client._config.app_slug = "test-app"
        
    def test_aggregate_single_expression(self):
        """Test adding single aggregate expression."""
        qb = QueryBuilder(self.mock_client, "orders")
        qb.aggregate("count(*)")
        
        params = qb.build_params()
        assert params["_aggregate"] == "count(*)"
        
    def test_aggregate_multiple_expressions(self):
        """Test adding multiple aggregate expressions."""
        qb = QueryBuilder(self.mock_client, "orders")
        qb.aggregate("count(*)", "sum(total)", "avg(price)")
        
        params = qb.build_params()
        assert params["_aggregate"] == "count(*),sum(total),avg(price)"
        
    def test_group_by_single_field(self):
        """Test GROUP BY with single field."""
        qb = QueryBuilder(self.mock_client, "orders")
        qb.group_by("status")
        
        params = qb.build_params()
        assert params["_group_by"] == "status"
        
    def test_group_by_multiple_fields(self):
        """Test GROUP BY with multiple fields."""
        qb = QueryBuilder(self.mock_client, "orders")
        qb.group_by("region", "category", "status")
        
        params = qb.build_params()
        assert params["_group_by"] == "region,category,status"
        
    def test_having_clause(self):
        """Test HAVING clause."""
        qb = QueryBuilder(self.mock_client, "orders")
        qb.having("sum_total > 1000")
        
        params = qb.build_params()
        assert params["_having"] == "sum_total > 1000"
        
    def test_aggregate_with_group_by(self):
        """Test combining aggregate with GROUP BY."""
        qb = QueryBuilder(self.mock_client, "orders")
        qb.aggregate("sum(total)", "count(*)").group_by("status")
        
        params = qb.build_params()
        assert params["_aggregate"] == "sum(total),count(*)"
        assert params["_group_by"] == "status"
        
    def test_aggregate_with_group_by_and_having(self):
        """Test full aggregation query with HAVING."""
        qb = QueryBuilder(self.mock_client, "orders")
        qb.aggregate("sum(total) as sum_total").group_by("customer_id").having("sum_total > 1000")
        
        params = qb.build_params()
        assert params["_aggregate"] == "sum(total) as sum_total"
        assert params["_group_by"] == "customer_id"
        assert params["_having"] == "sum_total > 1000"
        
    def test_aggregate_with_filters(self):
        """Test combining aggregates with filters."""
        qb = QueryBuilder(self.mock_client, "orders")
        qb.filter("status", "eq", "completed").aggregate("sum(total)").group_by("region")
        
        params = qb.build_params()
        assert params["status"] == "completed"
        assert params["_aggregate"] == "sum(total)"
        assert params["_group_by"] == "region"
        
    def test_chaining_methods(self):
        """Test method chaining returns QueryBuilder."""
        qb = QueryBuilder(self.mock_client, "orders")
        
        result = qb.aggregate("count(*)")
        assert isinstance(result, QueryBuilder)
        
        result = qb.group_by("status")
        assert isinstance(result, QueryBuilder)
        
        result = qb.having("count > 10")
        assert isinstance(result, QueryBuilder)


class TestAggregationExecution:
    """Test aggregation query execution and response handling."""

    def setup_method(self):
        """Setup mock client for each test."""
        self.mock_client = Mock()
        self.mock_http = Mock()
        self.mock_client._http_client = self.mock_http
        self.mock_client._config = Mock()
        self.mock_client._config.app_slug = "test-app"
        
    def test_execute_simple_aggregate(self):
        """Test executing simple aggregate query."""
        # Mock response
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [{"count": 150}],
            "total": 1
        }
        
        qb = QueryBuilder(self.mock_client, "orders")
        result = qb.aggregate("count(*)").execute()
        
        assert result["data"] == [{"count": 150}]
        assert result["total"] == 1
        assert result["data"][0]["count"] == 150
        
    def test_execute_multiple_aggregates(self):
        """Test executing multiple aggregates."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [{"count": 100, "avg_price": 25.50, "sum_stock": 5000}],
            "total": 1
        }
        
        qb = QueryBuilder(self.mock_client, "products")
        result = qb.aggregate("count(*)", "avg(price)", "sum(stock)").execute()
        
        assert result["data"][0]["count"] == 100
        assert result["data"][0]["avg_price"] == 25.50
        assert result["data"][0]["sum_stock"] == 5000
        
    def test_execute_group_by(self):
        """Test executing GROUP BY query."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [
                {"status": "completed", "sum_total": 5000, "count": 50},
                {"status": "pending", "sum_total": 2000, "count": 20}
            ],
            "total": 2
        }
        
        qb = QueryBuilder(self.mock_client, "orders")
        result = qb.aggregate("sum(total)", "count(*)").group_by("status").execute()
        
        assert len(result["data"]) == 2
        assert result["data"][0]["status"] == "completed"
        assert result["data"][0]["sum_total"] == 5000
        assert result["data"][1]["status"] == "pending"
        
    def test_execute_having(self):
        """Test executing query with HAVING clause."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [
                {"customer_id": 1, "sum_total": 5000, "order_count": 50},
                {"customer_id": 3, "sum_total": 3000, "order_count": 30}
            ],
            "total": 2
        }
        
        qb = QueryBuilder(self.mock_client, "orders")
        result = qb.aggregate("sum(total) as sum_total", "count(*) as order_count") \
            .group_by("customer_id") \
            .having("sum_total > 1000") \
            .execute()
        
        assert len(result["data"]) == 2
        for row in result["data"]:
            assert row["sum_total"] > 1000
            
    def test_execute_regular_query_response_structure(self):
        """Test regular query returns same response structure."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [
                {"id": 1, "name": "Product 1"},
                {"id": 2, "name": "Product 2"}
            ],
            "total": 2
        }
        
        qb = QueryBuilder(self.mock_client, "products")
        result = qb.execute()
        
        assert "data" in result
        assert "total" in result
        assert len(result["data"]) == 2
        assert result["total"] == 2
        
    def test_first_with_aggregation(self):
        """Test first() method with aggregation."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [{"count": 150}],
            "total": 1
        }
        
        qb = QueryBuilder(self.mock_client, "orders")
        result = qb.aggregate("count(*)").first()
        
        assert result == {"count": 150}
        
    def test_first_with_empty_result(self):
        """Test first() returns None for empty result."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [],
            "total": 0
        }
        
        qb = QueryBuilder(self.mock_client, "orders")
        result = qb.first()
        
        assert result is None


class TestAggregationIntegration:
    """Integration tests for complete aggregation workflows."""

    def setup_method(self):
        """Setup mock client for each test."""
        self.mock_client = Mock()
        self.mock_http = Mock()
        self.mock_client._http_client = self.mock_http
        self.mock_client._config = Mock()
        self.mock_client._config.app_slug = "test-app"
        
    def test_sales_by_region_workflow(self):
        """Test complete sales aggregation workflow."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [
                {"region": "North", "sum_amount": 50000, "count": 100},
                {"region": "South", "sum_amount": 35000, "count": 70}
            ],
            "total": 2
        }
        
        qb = QueryBuilder(self.mock_client, "sales")
        result = qb.filter("year", "eq", 2024) \
            .aggregate("sum(amount)", "count(*)") \
            .group_by("region") \
            .execute()
        
        # Verify API call
        self.mock_http.get.assert_called_once()
        call_args = self.mock_http.get.call_args
        params = call_args[1]["params"]
        
        assert params["year"] == 2024
        assert params["_aggregate"] == "sum(amount),count(*)"
        assert params["_group_by"] == "region"
        
        # Verify result
        assert len(result["data"]) == 2
        assert result["data"][0]["region"] == "North"
        
    def test_high_value_customers_workflow(self):
        """Test finding high-value customers with HAVING."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [
                {"customer_id": 1, "sum_total": 5000, "order_count": 50},
                {"customer_id": 3, "sum_total": 3000, "order_count": 30}
            ],
            "total": 2
        }
        
        qb = QueryBuilder(self.mock_client, "orders")
        result = qb.filter("status", "eq", "completed") \
            .aggregate("sum(total) as sum_total", "count(*) as order_count") \
            .group_by("customer_id") \
            .having("sum_total > 1000") \
            .execute()
        
        # Verify API call
        call_args = self.mock_http.get.call_args
        params = call_args[1]["params"]
        
        assert params["status"] == "completed"
        assert params["_having"] == "sum_total > 1000"
        
        # Verify all customers have sum_total > 1000
        for customer in result["data"]:
            assert customer["sum_total"] > 1000
            
    def test_multi_dimensional_analysis(self):
        """Test multi-dimensional aggregation."""
        self.mock_http.get.return_value = {
            "status": "success",
            "data": [
                {"region": "North", "category": "Electronics", "sum_amount": 25000},
                {"region": "North", "category": "Clothing", "sum_amount": 15000},
                {"region": "South", "category": "Electronics", "sum_amount": 20000}
            ],
            "total": 3
        }
        
        qb = QueryBuilder(self.mock_client, "sales")
        result = qb.aggregate("sum(amount)") \
            .group_by("region", "category") \
            .execute()
        
        # Verify API call
        call_args = self.mock_http.get.call_args
        params = call_args[1]["params"]
        
        assert params["_group_by"] == "region,category"
        assert len(result["data"]) == 3


class TestDatabaseModuleAggregation:
    """Test DatabaseModule integration with aggregations."""

    def setup_method(self):
        """Setup mock client."""
        self.mock_client = Mock()
        self.mock_client._http_client = Mock()
        self.mock_client._config = Mock()
        self.mock_client._config.app_slug = "test-app"
        
    def test_from_returns_query_builder(self):
        """Test from_() returns QueryBuilder with aggregation support."""
        db = DatabaseModule(self.mock_client)
        qb = db.from_("orders")
        
        assert isinstance(qb, QueryBuilder)
        assert hasattr(qb, "aggregate")
        assert hasattr(qb, "group_by")
        assert hasattr(qb, "having")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
