/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EventResponse } from './EventResponse';
import type { RootCauseAnalysisResponse } from './RootCauseAnalysisResponse';
/**
 * Response schema for a single incident with full details.
 */
export type IncidentDetailResponse = {
    id: string;
    title: string;
    status: string;
    severity: string;
    created_at: string;
    resolved_at?: (string | null);
    events?: Array<EventResponse>;
    root_cause_analyses?: Array<RootCauseAnalysisResponse>;
    service_names?: Array<string>;
};

