/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response schema for a root cause analysis.
 */
export type RootCauseAnalysisResponse = {
    id: string;
    incident_id: string;
    hypothesis: string;
    confidence: number;
    cited_event_ids: Array<any>;
    llm_provider_used: string;
    raw_llm_response?: (Record<string, any> | null);
    validation_failed?: boolean;
    created_at: string;
};

