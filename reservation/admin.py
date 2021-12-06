from django.contrib import admin
from django.utils.timezone import now

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    actions = ["force_end"]
    list_filter = ("event__start", "event__end")
    search_fields = (
        "start_location__station_name",
        "vehicle_type__name",
        "creator__username",
    )

    def get_list_display(self, request):
        if request.user.has_perm("cykel.view_user"):
            return (
                "id",
                "bike",
                "get_creator",
                "get_event_start",
                "get_event_end",
                "start_location",
                "vehicle_type",
            )
        return (
            "id",
            "bike",
            "get_event_start",
            "get_event_end",
            "start_location",
            "vehicle_type",
        )

    def get_event_start(self, obj):
        return obj.event.start

    get_event_start.admin_order_field = "event__start"
    get_event_start.short_description = "Reservation Start"

    def get_event_end(self, obj):
        return obj.event.end

    get_event_end.admin_order_field = "event__end"
    get_event_end.short_description = "Reservation End"

    def get_creator(self, obj):
        return obj.creator

    get_creator.admin_order_field = "creator"
    get_creator.short_description = "User"

    def get_fields(self, request, obj=None):
        default_fields = super(ReservationAdmin, self).get_fields(request, obj=obj)
        if not request.user.has_perm("cykel.view_user"):
            default_fields.remove("creator")
        return default_fields

    def force_end(self, request, queryset):
        for reservation in queryset:
            reservation.event.end = now()
            reservation.event.save()

    force_end.short_description = "Force end selected reservations"
    force_end.allowed_permissions = ("change",)
