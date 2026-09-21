/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ServiceDependencyResponse } from './ServiceDependencyResponse';
/**
 * Response schema for a single service.
 */
export type ServiceResponse = {
    id: string;
    name: string;
    description?: (string | null);
    created_at: string;
    dependencies?: Array<ServiceDependencyResponse>;
};

