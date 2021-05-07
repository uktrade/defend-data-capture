from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from accounts.models import User
from supply_chains.models import SupplyChain


class PaginationMixin:
    def paginate(self, paged_object: object, entries_per_page: int) -> object:
        page = self.request.GET.get("page", 1)
        paginator = Paginator(paged_object, entries_per_page)

        try:
            paged_object = paginator.page(page)
        except PageNotAnInteger:
            paged_object = paginator.page(1)
        except EmptyPage:
            paged_object = paginator.page(paginator.num_pages)

        return paged_object


def check_matching_gov_department(user: User, supply_chain: SupplyChain):
    """Check user's gov department matches that of a supply chain."""
    return user.gov_department == supply_chain.gov_department


class GovDepPermissionMixin:
    """
    A mixin which will rasie a 403 forbidden error if
    a user tries to access a URL for a supply chain not
    linked to their gov department.
    """

    def dispatch(self, *args, **kwargs):
        supply_chain = SupplyChain.objects.get(slug=kwargs.get("sc_slug"))

        if not check_matching_gov_department(self.request.user, supply_chain):
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)
