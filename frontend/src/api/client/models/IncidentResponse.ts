/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response schema for an incident (list view).
 */
export type IncidentResponse = {
    id: string;
    title: string;
    status: string;
    severity: string;
    created_at: string;
    resolved_at?: (string | null);
    event_count?: number;
    service_names?: Array<string>;
};

