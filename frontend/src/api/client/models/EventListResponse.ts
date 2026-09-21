/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EventResponse } from './EventResponse';
/**
 * Paginated response for events.
 */
export type EventListResponse = {
    events: Array<EventResponse>;
    total: number;
    page: number;
    page_size: number;
};

