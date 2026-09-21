/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ServiceResponse } from './ServiceResponse';
/**
 * Response schema for list of services with dependency graph.
 */
export type ServiceListResponse = {
    services: Array<ServiceResponse>;
    total: number;
};

