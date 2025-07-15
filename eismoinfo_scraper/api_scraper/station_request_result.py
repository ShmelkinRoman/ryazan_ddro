
from .models import StationRequestResult


class StationRequestResultQueryService:
    def get_request_results(
            self, start, end,
            station_id=None, request_status=None
            ):
        filter_params = {}
        if station_id:
            filter_params['station__eismo_station_id'] = station_id
        if request_status == 'ERROR':
            filter_params['status__icontains'] = request_status
        elif request_status:
            filter_params['status'] = request_status
        filter_params['request_time__gte'] = start
        filter_params['request_time__lte'] = end

        queryset = StationRequestResult.objects.filter(**filter_params)
        return queryset
