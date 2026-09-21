/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response schema for a single event.
 */
export type EventResponse = {
    id: string;
    service_id: string;
    event_type: string;
    payload: Record<string, any>;
    is_anomalous: boolean;
    anomaly_score?: (number | null);
    timestamp: string;
};

