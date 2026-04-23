from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ResourceNotFoundException
from app.models.enums import BidStatus, OrderStatus
from app.services.orders.service import OrderBidService


@pytest.mark.asyncio
class TestOrderBidService:
    async def test_place_bid_success(self, repository_factory, override_dependencies, db_session):
        order = SimpleNamespace(id=1, status=OrderStatus.BIDDING)
        delivery_user = SimpleNamespace(id=1, upi_screenshot_url="http://example.com/upi.jpg")

        order_repository = repository_factory(get_by_id=AsyncMock(return_value=order))
        user_repository = repository_factory(get_by_id=AsyncMock(return_value=delivery_user))
        order_bid_repository = repository_factory(
            list_bids_for_order=AsyncMock(return_value=[]),
            create_bid=AsyncMock(
                return_value=SimpleNamespace(id=1, order_id=1, delivery_user_id=1, amount=100.0)
            ),
        )

        override_dependencies(
            order_repository=order_repository,
            user_repository=user_repository,
            order_bid_repository=order_bid_repository,
        )

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=order_repository,
            user_repository=user_repository,
        )

        bid = await order_bid_service.place_bid(order_id=1, delivery_user_id=1, bid_amount=100.0)

        assert bid is not None
        assert bid.order_id == 1
        assert bid.delivery_user_id == 1
        order_bid_repository.create_bid.assert_called_once_with(
            1, 1, 100.0, "http://example.com/upi.jpg"
        )

    async def test_place_bid_order_not_bidding(
        self, repository_factory, override_dependencies, db_session
    ):
        order = SimpleNamespace(id=1, status=OrderStatus.DELIVERED)

        order_repository = repository_factory(get_by_id=AsyncMock(return_value=order))
        user_repository = repository_factory(
            get_by_id=AsyncMock(return_value=SimpleNamespace(id=1))
        )

        override_dependencies(order_repository=order_repository, user_repository=user_repository)

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=AsyncMock(),
            order_repository=order_repository,
            user_repository=user_repository,
        )

        with pytest.raises(ValueError, match="Bids can only be placed on orders in BIDDING status"):
            await order_bid_service.place_bid(order_id=1, delivery_user_id=1, bid_amount=100.0)

    async def test_place_bid_order_not_found(
        self, repository_factory, override_dependencies, db_session
    ):
        order_repository = repository_factory(get_by_id=AsyncMock(return_value=None))
        user_repository = repository_factory(
            get_by_id=AsyncMock(return_value=SimpleNamespace(id=1))
        )

        override_dependencies(order_repository=order_repository, user_repository=user_repository)

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=AsyncMock(),
            order_repository=order_repository,
            user_repository=user_repository,
        )

        with pytest.raises(ResourceNotFoundException, match="Order not found"):
            await order_bid_service.place_bid(order_id=1, delivery_user_id=1, bid_amount=100.0)

    async def test_place_bid_already_bid(
        self, repository_factory, override_dependencies, db_session
    ):
        order = SimpleNamespace(id=1, status=OrderStatus.BIDDING)
        delivery_user = SimpleNamespace(id=1, upi_screenshot_url="http://example.com/upi.jpg")
        existing_bid = SimpleNamespace(delivery_user_id=1)

        order_repository = repository_factory(get_by_id=AsyncMock(return_value=order))
        user_repository = repository_factory(get_by_id=AsyncMock(return_value=delivery_user))
        order_bid_repository = repository_factory(
            list_bids_for_order=AsyncMock(return_value=[existing_bid])
        )

        override_dependencies(
            order_repository=order_repository,
            user_repository=user_repository,
            order_bid_repository=order_bid_repository,
        )

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=order_repository,
            user_repository=user_repository,
        )

        with pytest.raises(ValueError, match="You have already placed a bid on this order"):
            await order_bid_service.place_bid(order_id=1, delivery_user_id=1, bid_amount=100.0)

    async def test_place_bid_no_upi_screenshot(
        self, repository_factory, override_dependencies, db_session
    ):
        order = SimpleNamespace(id=1, status=OrderStatus.BIDDING)
        delivery_user = SimpleNamespace(id=1, upi_screenshot_url=None)

        order_repository = repository_factory(get_by_id=AsyncMock(return_value=order))
        user_repository = repository_factory(get_by_id=AsyncMock(return_value=delivery_user))
        order_bid_repository = repository_factory(list_bids_for_order=AsyncMock(return_value=[]))

        override_dependencies(
            order_repository=order_repository,
            user_repository=user_repository,
            order_bid_repository=order_bid_repository,
        )

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=order_repository,
            user_repository=user_repository,
        )

        with pytest.raises(
            ValueError, match="Delivery user has not provided UPI screenshot, cannot place bid"
        ):
            await order_bid_service.place_bid(order_id=1, delivery_user_id=1, bid_amount=100.0)

    async def test_delete_bid_success(self, repository_factory, override_dependencies, db_session):
        bid = SimpleNamespace(id=1)
        order_bid_repository = repository_factory(
            get_bid_by_id=AsyncMock(return_value=bid), delete_bid=AsyncMock(return_value=None)
        )

        override_dependencies(order_bid_repository=order_bid_repository)

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
        )

        await order_bid_service.delete_bid(bid_id=1)
        order_bid_repository.delete_bid.assert_called_once_with(1)

    async def test_delete_bid_not_found(
        self, repository_factory, override_dependencies, db_session
    ):
        order_bid_repository = repository_factory(get_bid_by_id=AsyncMock(return_value=None))

        override_dependencies(order_bid_repository=order_bid_repository)

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
        )

        with pytest.raises(ResourceNotFoundException, match="Bid not found"):
            await order_bid_service.delete_bid(bid_id=1)

    async def test_list_bids_for_order(self, repository_factory, override_dependencies, db_session):
        bids = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        order_bid_repository = repository_factory(list_bids_for_order=AsyncMock(return_value=bids))

        override_dependencies(order_bid_repository=order_bid_repository)

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
        )

        result = await order_bid_service.list_bids_for_order(order_id=1)
        assert len(result) == 2
        order_bid_repository.list_bids_for_order.assert_called_once_with(1)

    async def test_get_bid_by_id(self, repository_factory, override_dependencies, db_session):
        bid = SimpleNamespace(id=1)
        order_bid_repository = repository_factory(get_bid_by_id=AsyncMock(return_value=bid))

        override_dependencies(order_bid_repository=order_bid_repository)

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
        )

        result = await order_bid_service.get_bid_by_id(bid_id=1)
        assert result.id == 1
        order_bid_repository.get_bid_by_id.assert_called_once_with(1)

    async def test_get_accepted_bid_by_order_id(
        self, repository_factory, override_dependencies, db_session
    ):
        bid = SimpleNamespace(id=1, status=BidStatus.ACCEPTED)
        order_bid_repository = repository_factory(
            get_accepted_bid_by_order_id=AsyncMock(return_value=bid)
        )

        override_dependencies(order_bid_repository=order_bid_repository)

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
        )

        result = await order_bid_service.get_accepted_bid_by_order_id(order_id=1)
        assert result.status == BidStatus.ACCEPTED
        order_bid_repository.get_accepted_bid_by_order_id.assert_called_once_with(1)

    async def test_get_bids_by_delivery_user_id(
        self, repository_factory, override_dependencies, db_session
    ):
        bids = [
            SimpleNamespace(id=1, delivery_user_id=1),
            SimpleNamespace(id=2, delivery_user_id=1),
        ]
        order_bid_repository = repository_factory(
            get_bids_by_delivery_user_id=AsyncMock(return_value=bids)
        )

        override_dependencies(order_bid_repository=order_bid_repository)

        order_bid_service = OrderBidService(
            db=db_session,
            orderbid_repository=order_bid_repository,
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
        )

        result = await order_bid_service.get_bids_by_delivery_user_id(delivery_user_id=1)
        assert len(result) == 2
        order_bid_repository.get_bids_by_delivery_user_id.assert_called_once_with(1)
