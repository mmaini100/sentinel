/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EventListResponse } from '../models/EventListResponse';
import type { ServiceListResponse } from '../models/ServiceListResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ServicesService {
    /**
     * List Services
     * List all services with their dependency graph.
     * @returns ServiceListResponse Successful Response
     * @throws ApiError
     */
    public static listServicesApiV1ServicesGet(): CancelablePromise<ServiceListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/services',
        });
    }
    /**
     * List Service Events
     * Get paginated events for a specific service.
     * @param serviceId
     * @param page
     * @param pageSize
     * @param anomalousOnly
     * @returns EventListResponse Successful Response
     * @throws ApiError
     */
    public static listServiceEventsApiV1ServicesServiceIdEventsGet(
        serviceId: string,
        page: number = 1,
        pageSize: number = 50,
        anomalousOnly: boolean = false,
    ): CancelablePromise<EventListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/services/{service_id}/events',
            path: {
                'service_id': serviceId,
            },
            query: {
                'page': page,
                'page_size': pageSize,
                'anomalous_only': anomalousOnly,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
