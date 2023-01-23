import { useState } from "react";
import { JobRun } from "types";
import { JobRunStatus } from "types/enums";
import { JobStatusFilter } from "../JobStatusFilter/JobStatusFilter.index";

export const useSubJobFilter = (jobRuns: JobRun[]) => {
  const [filter, setFilter] = useState<string[]>(allStatuses);

  const filterPanel = (
    <JobStatusFilter
      jobRuns={jobRuns}
      onFilterChange={setFilter}
      statusFilters={filter}
    />
  );

  const filteredJobRuns = jobRuns.filter(run => filter.includes(run.status));

  return { filterPanel, filteredJobRuns };
};

const allStatuses = Object.values(JobRunStatus)
  .map(key => JobRunStatus[key])
  .filter(value => typeof value === "string") as string[];
