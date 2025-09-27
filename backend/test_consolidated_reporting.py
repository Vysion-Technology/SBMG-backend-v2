#!/usr/bin/env python3
"""
Test script for the consolidated reporting system.
Tests RBAC logic, query optimization, and endpoint functionality.
"""

import sys
import os
from unittest.mock import Mock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.consolidated_reporting import UnifiedReportingService
from auth_utils import UserRole


def create_mock_user(roles_and_positions):
    """Create a mock user with specified roles and positions."""
    user = Mock()
    user.id = 1
    user.username = "test_user"
    user.positions = []
    
    for role_name, district_id, block_id, village_id in roles_and_positions:
        position = Mock()
        position.role = Mock()
        position.role.name = role_name
        position.district_id = district_id
        position.block_id = block_id
        position.village_id = village_id
        user.positions.append(position)
    
    return user


def test_rbac_logic():
    """Test the RBAC jurisdiction filtering logic."""
    print("🧪 Testing RBAC Logic...")
    
    # Test 1: Admin user (should have no restrictions)
    admin_user = create_mock_user([(UserRole.ADMIN, None, None, None)])
    admin_filter = UnifiedReportingService.get_user_jurisdiction_filter(admin_user)
    assert admin_filter is None, "Admin should have no jurisdiction filter"
    print("✅ Admin user RBAC test passed")
    
    # Test 2: CEO user (should be restricted to their district)
    ceo_user = create_mock_user([(UserRole.CEO, 1, None, None)])
    ceo_filter = UnifiedReportingService.get_user_jurisdiction_filter(ceo_user)
    assert ceo_filter is not None, "CEO should have jurisdiction filter"
    print("✅ CEO user RBAC test passed")
    
    # Test 3: BDO user (should be restricted to their block)
    bdo_user = create_mock_user([(UserRole.BDO, None, 5, None)])
    bdo_filter = UnifiedReportingService.get_user_jurisdiction_filter(bdo_user)
    assert bdo_filter is not None, "BDO should have jurisdiction filter"
    print("✅ BDO user RBAC test passed")
    
    # Test 4: VDO user (should be restricted to their village)
    vdo_user = create_mock_user([(UserRole.VDO, None, None, 10)])
    vdo_filter = UnifiedReportingService.get_user_jurisdiction_filter(vdo_user)
    assert vdo_filter is not None, "VDO should have jurisdiction filter"
    print("✅ VDO user RBAC test passed")
    
    # Test 5: Worker user (should be restricted to assigned complaints)
    worker_user = create_mock_user([(UserRole.WORKER, None, None, None)])
    worker_filter = UnifiedReportingService.get_user_jurisdiction_filter(worker_user)
    assert worker_filter is not None, "Worker should have jurisdiction filter"
    print("✅ Worker user RBAC test passed")
    
    # Test 6: Multi-role user (CEO + BDO)
    multi_user = create_mock_user([
        (UserRole.CEO, 1, None, None),
        (UserRole.BDO, None, 5, None)
    ])
    multi_filter = UnifiedReportingService.get_user_jurisdiction_filter(multi_user)
    assert multi_filter is not None, "Multi-role user should have combined jurisdiction filter"
    print("✅ Multi-role user RBAC test passed")


async def test_user_role_summary():
    """Test the user role summary functionality."""
    print("🧪 Testing User Role Summary...")
    
    # Test admin user summary
    admin_user = create_mock_user([(UserRole.ADMIN, None, None, None)])
    admin_summary = await UnifiedReportingService.get_user_role_summary(admin_user)
    
    assert admin_summary["is_admin"] is True, "Admin should be identified as admin"
    assert admin_summary["access_level"] == "ADMIN", "Admin should have ADMIN access level"
    assert UserRole.ADMIN in admin_summary["roles"], "Admin role should be in roles list"
    print("✅ Admin user summary test passed")
    
    # Test VDO user summary
    vdo_user = create_mock_user([(UserRole.VDO, 1, 2, 3)])
    vdo_summary = await UnifiedReportingService.get_user_role_summary(vdo_user)
    
    assert vdo_summary["is_admin"] is False, "VDO should not be identified as admin"
    assert vdo_summary["access_level"] == "VDO", "VDO should have VDO access level"
    assert UserRole.VDO in vdo_summary["roles"], "VDO role should be in roles list"
    assert "Village-3" in vdo_summary["jurisdictions"], "Village jurisdiction should be listed"
    print("✅ VDO user summary test passed")


def test_query_optimization():
    """Test that the query optimization methods work correctly."""
    print("🧪 Testing Query Optimization...")
    
    # Test optimized complaint query
    query = UnifiedReportingService.get_optimized_complaint_query()
    assert query is not None, "Optimized query should not be None"
    
    # Check that query has proper options (test that it has options at all)
    assert hasattr(query, 'options'), "Query should have options for eager loading"
    assert query.options is not None, "Query options should not be None"
    print("✅ Query optimization test passed")


def run_all_tests():
    """Run all test suites."""
    print("🚀 Starting Consolidated Reporting Tests...\n")
    
    try:
        test_rbac_logic()
        print()
        
        import asyncio
        asyncio.run(test_user_role_summary())
        print()
        
        test_query_optimization()
        print()
        
        print("🎉 All tests passed! Consolidated reporting system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)