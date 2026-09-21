/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { IncidentResponse } from './IncidentResponse';
/**
 * Paginated response for incidents.
 */
export type IncidentListResponse = {
    incidents: Array<IncidentResponse>;
    total: number;
    page: number;
    page_size: number;
};

