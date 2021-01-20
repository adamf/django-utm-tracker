from __future__ import annotations

from typing import Type

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.db import models
from django.db.models.base import Model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _lazy

from .types import UtmParamsDict


class LeadSourceManager(models.Manager):
    def create_from_utm_params(
        self, user: Type[Model], session: SessionBase, utm_params: UtmParamsDict
    ) -> LeadSource:
        """Persist a LeadSource dictionary of utm_* values."""
        try:
            return LeadSource.objects.create(
                user=user,
                session_key=session.session_key,
                medium=utm_params["utm_medium"],
                source=utm_params["utm_source"],
                campaign=utm_params.get("utm_campaign", ""),
                term=utm_params.get("utm_term", ""),
                content=utm_params.get("utm_content", ""),
            )
        except KeyError as ex:
            raise ValueError(f"Missing utm param: {ex}")


class LeadSource(models.Model):
    """
    Model used to track inbound leads.

    The model is separate from the ClientOnboarding and FreelancerOnboarding
    models so that we can track both in one place, and also so that we can
    backfill all historical data (before those models existed).

    NB The User field is *not* unique - it is possible for one User to have
    come through multiple routes (i.e. seen multiple ads); how we determine
    which ad is the one that made them register is a point of debate - so
    in this model we just record the data - and let the analysis happen later.

    The fields in this model are based on the industry standard UTM fields (
    see https://en.wikipedia.org/wiki/UTM_parameters for details).

    Most of the fields are optional, and included for completeness. Internal
    referrals do not have utm_* values associated with them, but the fields
    can be reused to identify the referrer.

    For example:

        medium: "referral"
        source: "internal"
        campaign: "profile" (e.g. book me)
        term: {{ referral token }}
        content: "book me"

    We are not using choices in this model as we can't predict what the params
    coming in from external sources may be, and we can't restrict the marketing
    team to specific values.

    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lead_sources",
    )
    medium = models.CharField(
        max_length=30,
        help_text=_lazy(
            "utm_medium: Identifies what type of link was used, "
            "such as cost per click or email."
        ),
    )
    source = models.CharField(
        max_length=30,
        help_text=_lazy(
            "utm_source: Identifies which site sent the traffic, "
            "and is a required parameter."
        ),
    )
    campaign = models.CharField(
        max_length=100,  # can be autogenerated by email campaigns
        help_text=_lazy(
            "utm_campaign: Identifies a specific product promotion "
            "or strategic campaign."
        ),
        blank=True,
    )
    term = models.CharField(
        max_length=50, help_text=_lazy("utm_term: Identifies search terms."), blank=True
    )
    content = models.CharField(
        max_length=50,
        help_text=_lazy(
            "utm_content: Identifies what specifically was clicked to bring "
            "the user to the site, such as a banner ad or a text link."
        ),
        blank=True,
    )
    timestamp = models.DateTimeField(
        default=timezone.now, help_text=_lazy("When the event occurred.")
    )
    session_key = models.CharField(
        max_length=40,
        default="",
        blank=True,
        help_text=_lazy("The session in which the params were captured."),
    )
    created_at = models.DateTimeField(
        default=timezone.now, help_text=_lazy("When the event was recorded.")
    )

    objects = LeadSourceManager()

    class Meta:
        get_latest_by = ("timestamp",)

    def __str__(self) -> str:
        return f"Lead source {self.id} for {self.user}: {self.medium}/{self.source}"

    def __repr__(self) -> str:
        return (
            f"<LeadSource id={self.id} user={self.user_id} "
            f"medium='{self.medium}' source='{self.source}'>"
        )
