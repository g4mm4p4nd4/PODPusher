import React from 'react';
import { TrendingKeyword } from '../services/analytics';

interface AnalyticsChartProps {
  keywords: TrendingKeyword[];
  title: string;
  termLabel: string;
  clicksLabel: string;
  tableLabel: string;
}

export default function AnalyticsChart({
  keywords,
  title,
  termLabel,
  clicksLabel,
  tableLabel,
}: AnalyticsChartProps) {
  const maxClicks = Math.max(1, ...keywords.map((keyword) => keyword.clicks));

  return (
    <section aria-labelledby="analytics-table-title" className="bg-white dark:bg-gray-900 shadow rounded-lg p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <h2 id="analytics-table-title" className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h2>
        <span className="text-sm text-gray-500 dark:text-gray-400">{tableLabel}</span>
      </div>
      <div className="mt-4 overflow-x-auto" role="presentation">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700" aria-label={tableLabel}>
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-300"
              >
                {termLabel}
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-300"
              >
                {clicksLabel}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {keywords.map((keyword) => {
              const width = `${Math.round((keyword.clicks / maxClicks) * 100)}%`;

              return (
                <tr key={keyword.term} className="bg-white dark:bg-gray-900">
                  <th scope="row" className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                    {keyword.term}
                  </th>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3" aria-label={`${keyword.clicks} ${clicksLabel}`}>
                      <div className="flex-1 h-2 rounded-full bg-indigo-100 dark:bg-indigo-950" aria-hidden="true">
                        <div
                          className="h-2 rounded-full bg-indigo-500 dark:bg-indigo-400 transition-all"
                          style={{ width }}
                        />
                      </div>
                      <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{keyword.clicks}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
