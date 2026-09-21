/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { IncidentDetailResponse } from '../models/IncidentDetailResponse';
import type { IncidentListResponse } from '../models/IncidentListResponse';
import type { IncidentResponse } from '../models/IncidentResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class IncidentsService {
    /**
     * List Incidents
     * List incidents with pagination and optional filters.
     * @param page
     * @param pageSize
     * @param status
     * @param severity
     * @returns IncidentListResponse Successful Response
     * @throws ApiError
     */
    public static listIncidentsApiV1IncidentsGet(
        page: number = 1,
        pageSize: number = 20,
        status?: (string | null),
        severity?: (string | null),
    ): CancelablePromise<IncidentListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/incidents',
            query: {
                'page': page,
                'page_size': pageSize,
                'status': status,
                'severity': severity,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Stream Incidents
     * Server-Sent Events endpoint for real-time incident streaming.
     * Polls the database for new incidents and yields them as JSON.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static streamIncidentsApiV1IncidentsStreamGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/incidents/stream',
        });
    }
    /**
     * Get Incident
     * Get full incident detail including events and root cause analyses.
     * @param incidentId
     * @returns IncidentDetailResponse Successful Response
     * @throws ApiError
     */
    public static getIncidentApiV1IncidentsIncidentIdGet(
        incidentId: string,
    ): CancelablePromise<IncidentDetailResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/incidents/{incident_id}',
            path: {
                'incident_id': incidentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Resolve Incident
     * Mark an incident as resolved.
     * @param incidentId
     * @returns IncidentResponse Successful Response
     * @throws ApiError
     */
    public static resolveIncidentApiV1IncidentsIncidentIdResolvePost(
        incidentId: string,
    ): CancelablePromise<IncidentResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/incidents/{incident_id}/resolve',
            path: {
                'incident_id': incidentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
