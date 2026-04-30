import { type Page, type Route } from './playwright';

type JsonValue = Record<string, unknown> | unknown[];

const provenance = {
  source: 'e2e_ui_parity_fixture',
  is_estimated: false,
  updated_at: '2026-04-25T12:00:00.000Z',
  confidence: 0.94,
};

const metrics = [
  { label: 'Trending Keywords', value: 2847, delta: 18.6, sparkline: [12, 18, 16, 24] },
  { label: 'Active Listings Generated', value: 6253, delta: 12.4, sparkline: [8, 9, 12, 15] },
  { label: 'Open A/B Tests', value: 23, delta: 4, sparkline: [3, 5, 4, 7] },
  { label: 'Weekly Digest Subscribers', value: 18652, delta: 9.3, sparkline: [4, 6, 7, 9] },
  {
    label: 'Remaining Image Quota',
    value: 82500,
    delta: 0,
    sparkline: [82, 82],
    quota: { used: 17500, limit: 100000, percent: 82 },
  },
].map((metric) => ({ ...metric, provenance }));

const trendKeywords = [
  {
    rank: 1,
    keyword: 'dog mom',
    search_volume: 156000,
    growth: 64.2,
    competition: 38,
    suggested_products: ['T-Shirt', 'Mug', 'Tote Bag'],
    opportunity: 'High',
    market_examples: [
      {
        title: 'Dog Mom Shirt Bestseller',
        keyword: 'dog mom',
        source: 'amazon',
        source_url: 'https://example.com/dog-mom-shirt',
        image_url: null,
        engagement_score: 156000,
        example_type: 'source_product',
        provenance,
      },
    ],
    strategy: {
      evidence_summary: 'Dog Mom Shirt Bestseller',
      variation_prompts: [
        'Reframe dog mom for a narrower buyer identity or occasion.',
        'Translate the strongest phrase into an original T-shirt layout.',
      ],
      anti_patterns: ['Do not copy source titles, artwork, photos, or protected references.'],
    },
  },
  {
    rank: 2,
    keyword: 'pickleball life',
    search_volume: 128000,
    growth: 52.7,
    competition: 44,
    suggested_products: ['Hoodie', 'Tumbler'],
    opportunity: 'High',
    market_examples: [
      {
        title: 'Pickleball Life Tumbler Example',
        keyword: 'pickleball life',
        source: 'etsy',
        source_url: 'https://example.com/pickleball-life',
        image_url: null,
        engagement_score: 128000,
        example_type: 'source_product',
        provenance,
      },
    ],
    strategy: {
      evidence_summary: 'Pickleball Life Tumbler Example',
      variation_prompts: ['Pair pickleball life with a court-side buyer identity.'],
      anti_patterns: ['Avoid generic sports phrasing without a buyer angle.'],
    },
  },
];

const seasonalEvent = {
  name: 'Back to School',
  event_date: '2025-08-01',
  days_away: 105,
  priority: 'high',
  saved: false,
  recommended_keywords: [
    { keyword: 'back to school', volume: 54200 },
    { keyword: 'teacher life', volume: 15400 },
  ],
  product_categories: [
    { category: 'T-Shirts', listings: 15200, demand: 88 },
    { category: 'Hoodies', listings: 8900, demand: 74 },
  ],
  niche_angles: ['Teacher Appreciation', 'Student Motivation'],
};

const searchResults = [
  {
    id: 1,
    name: 'Retro Dog Mom T-Shirt',
    category: 'Apparel',
    rating: 4.6,
    trend_score: 92,
    demand_signal: 'High',
    keyword: 'dog mom summer vibes',
    price: 18.99,
  },
  {
    id: 2,
    name: 'Pickleball Mom Tumbler',
    category: 'Drinkware',
    rating: 4.7,
    trend_score: 88,
    demand_signal: 'High',
    keyword: 'pickleball gifts',
    price: 21.99,
  },
];

const baseExperiment = {
  id: 7,
  name: 'Retro Sunset Tee - Thumbnail Test',
  product_id: 101,
  product: 'Retro Beach Sunset Tee',
  experiment_type: 'thumbnail',
  status: 'running',
  start_time: '2025-05-12T00:00:00.000Z',
  end_time: null,
  impressions: 300,
  clicks: 18,
  ctr: 6,
  ctr_lift: 25,
  confidence: 98,
  significant: true,
  winner: { id: 72, name: 'Thumbnail B', weight: 0.5, impressions: 150, clicks: 10, ctr: 6.67 },
  variants: [
    { id: 71, name: 'Thumbnail A', weight: 0.5, impressions: 150, clicks: 8, ctr: 5.33 },
    { id: 72, name: 'Thumbnail B', weight: 0.5, impressions: 150, clicks: 10, ctr: 6.67 },
  ],
  insights: ['Thumbnail B is driving higher CTR with a 25% lift.'],
  integration_status: {
    listing_push: 'local_state',
    message: 'Winner push updates local experiment state.',
  },
  provenance,
};

const notificationsDashboard = {
  cards: metrics.slice(0, 4),
  digest_schedule: [
    {
      digest: 'Weekly Digest',
      schedule: 'Mon 9:00 AM',
      audience: 'All Users',
      channels: ['Email', 'In-App'],
      active: true,
    },
  ],
  scheduled_jobs: [
    { id: 11, name: 'Trend Data Refresh', frequency: 'Every 6 hours', status: 'on_track' },
    { id: 12, name: 'Seasonal Event Sync', frequency: 'Daily', status: 'on_track' },
  ],
  notifications: [
    {
      id: 42,
      message: 'A/B test Dog Mom Tee v2 is winning.',
      type: 'success',
      created_at: '2026-04-25T12:00:00.000Z',
      read_status: false,
    },
  ],
  rules: [
    {
      id: 5,
      name: 'Low Image Quota Warning',
      metric: 'image_quota_remaining',
      operator: 'less than',
      threshold: 20,
      window: '1 day',
      channels: ['Email', 'In-App'],
      active: true,
    },
  ],
  upcoming_schedule: [
    { name: 'Weekly Digest', category: 'digest', next_run: '2026-04-26T09:00:00.000Z' },
    { name: 'Seasonal Event Sync', category: 'maintenance', next_run: '2026-04-26T12:00:00.000Z' },
  ],
  preferences: {
    email: { enabled: true },
    in_app: { enabled: true },
    slack: { enabled: false, connected: false, status: 'credentials_missing' },
  },
};

const settingsDashboard = {
  localization: {
    default_language: 'en',
    marketplace_regions: ['US', 'CA'],
    currency: 'USD',
    date_format: 'MMM DD, YYYY',
    localized_niche_targeting: true,
    primary_targeting_region: 'US',
    preview: {
      language: 'English (US)',
      currency: '$23.99',
      date: 'May 18, 2025',
      example_niche: 'Dog Mom Gifts',
    },
  },
  regional_niche_preferences: {
    categories: [
      { category: 'Apparel', weight: 68 },
      { category: 'Home & Living', weight: 54 },
    ],
    excluded_global_niches: ['Politics', 'Adult Content'],
  },
  brand_profiles: [
    { id: 1, name: 'PODPusher Default', tone: 'Friendly', audience: 'Dog moms', active: true },
  ],
  integrations: [
    { provider: 'etsy', account_name: 'podpusher.etsy.com', status: 'connected' },
    { provider: 'slack', account_name: null, status: 'stub' },
  ],
  quotas: {
    image_generation: { used: 82500, limit: 100000, percent: 82, provenance },
    ai_credits: { used: 62450, limit: 100000, percent: 62, provenance },
    active_listings: { used: 6253, limit: 10000, percent: 62, provenance },
    ab_tests: { used: 23, limit: 100, percent: 23, provenance },
  },
  usage: { image_generation: 82500, ai_credits: 62450 },
  stores: [{ name: 'PODPusher Etsy', marketplace: 'Etsy', region: 'US' }],
  team_members: [
    {
      id: 1,
      name: 'Admin',
      email: 'admin@podpusher.com',
      role: 'Administrator',
      permissions: ['All permissions'],
      status: 'active',
      last_active_at: '2026-04-25T12:00:00.000Z',
    },
  ],
};

export async function setupUiParityApiMocks(page: Page) {
  let abExperiments = [baseExperiment];
  let savedCurrency = 'USD';
  let nextDraftId = 101;

  await page.addInitScript(() => window.localStorage.clear());

  await page.route('**/api/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (method === 'OPTIONS') {
      return fulfillCorsPreflight(route);
    }

    if (path === '/api/user/me') {
      return fulfillJson(route, { plan: 'professional', quota_used: 17500, quota_limit: 100000 });
    }

    if (path === '/api/dashboard/overview') {
      return fulfillJson(route, {
        metrics,
        keyword_growth: [
          { date: '2025-05-12', value: 1600 },
          { date: '2025-05-18', value: 4100 },
        ],
        top_rising_niches: [
          { niche: 'Dog Mom Gifts', growth: 64.2, competition_label: 'Low' },
          { niche: 'Teacher Appreciation', growth: 52.7, competition_label: 'Low' },
        ],
        popular_categories: [
          { category: 'Apparel', listings: 28451, demand: 78 },
          { category: 'Mugs', listings: 8940, demand: 66 },
        ],
        seasonal_events: [seasonalEvent],
        recent_drafts: [{ id: 21, title: 'Funny Dog Mom Tee', language: 'en' }],
        ab_performance: [{ test: 'Dog Mom Tee v2', ctr: 3.24, lift: 0.84 }],
        notifications: notificationsDashboard.notifications,
        provenance,
      });
    }

    if (path === '/api/trends/insights') {
      return fulfillJson(route, {
        cards: metrics.slice(0, 4),
        momentum: [
          { date: '2025-05-12', etsy_search_volume: 22000, google_trends: 35, internal_trend_score: 50 },
          { date: '2025-05-18', etsy_search_volume: 72000, google_trends: 58, internal_trend_score: 82 },
        ],
        product_categories: [{ category: 'T-Shirts', listings: 124510, demand: 89 }],
        keywords: trendKeywords,
        design_ideas: [
          {
            title: 'Dog Mom Floral Typo',
            keyword: 'dog mom',
            niche: 'Dog Mom Gifts',
            product_type: 'T-Shirt',
            opportunity: 'High',
            market_examples: trendKeywords[0].market_examples,
            strategy: trendKeywords[0].strategy,
            provenance,
          },
        ],
        tag_clusters: [{ cluster: 'dog mom', tags: ['dog mom', 'fur mama'], volume: 156000 }],
        provenance,
      });
    }

    if (path === '/api/seasonal/events') {
      return fulfillJson(route, {
        opportunity_score: 87,
        listings_to_prepare: 26,
        events: [seasonalEvent],
        high_priority_events: [seasonalEvent],
        timeline: [{ name: 'Back to School', start_by: 'Jun 30', priority: 'high', launch_window: '30-60 days' }],
        provenance,
      });
    }

    if (path === '/api/seasonal/events/save') {
      return fulfillJson(route, { saved: true, demo_state: true });
    }

    if (path === '/api/niches/suggestions') {
      return fulfillJson(route, {
        cards: metrics.slice(0, 4),
        profile: {
          tone: 'Humorous, Positive',
          audience: 'Adults, Parents',
          interests: ['Pets', 'Coffee', 'Outdoors'],
          banned_topics: ['Politics', 'Religion'],
          preferred_products: ['Apparel', 'Mugs', 'Totes'],
        },
        niches: [
          {
            niche: 'Outdoor Adventure',
            keyword: 'adventure is calling',
            demand_trend: [12, 18, 22, 28],
            competition: 42,
            profitability: 'High',
            estimated_profit: 4.65,
            audience_overlap: 58,
            brand_fit_score: 87,
            brand_fit_label: 'Great',
            products: ['Apparel', 'Mugs'],
            why: ['Strong search trend.', 'Good product fit.'],
            saved: false,
          },
        ],
        suggested_phrases: [{ phrase: 'adventure is calling', demand: 'High' }],
        design_inspiration: [{ title: 'Adventure Awaits' }],
        localized_variants: [{ market: 'US', language: 'English', phrase: 'Adventure Awaits', demand: 'High' }],
        provenance,
      });
    }

    if (path === '/api/niches/profile' || path === '/api/niches/saved') {
      return fulfillJson(route, { saved: true, demo_state: true });
    }

    if (path === '/api/search/insights') {
      return fulfillJson(route, {
        total: searchResults.length,
        results: searchResults,
        phrase_suggestions: ['dog mom summer vibes', 'retro beach dog'],
        design_inspiration: [{ title: 'Retro Dog Mom Badge' }],
        related_niches: ['Dog Lovers', 'Pickleball'],
        saved_searches: [
          {
            id: 1,
            name: 'Dog Mom Summer',
            query: 'dog mom',
            filters: { category: 'Apparel', marketplace: 'etsy', season: 'Summer', niche: 'Dog Lovers' },
            result_count: 48,
          },
        ],
        recent_queries: [{ query: 'teacher coffee mug', age: '3h ago' }],
        comparison: searchResults,
        provenance,
      });
    }

    if (path === '/api/search/saved' || path === '/api/search/watchlist') {
      return fulfillJson(route, { saved: true, demo_state: true });
    }

    if (path === '/api/ideation/suggest-tags') {
      return fulfillJson(route, ['dog mom', 'retro beach', 'summer tee']);
    }

    if (path === '/api/listing-composer/generate') {
      return fulfillJson(route, {
        title: 'Retro Dog Mom T-Shirt for Summer',
        description: 'A trend-aware shirt for dog moms.',
        tags: ['dog mom', 'summer tee'],
        score: { optimization_score: 91 },
        compliance: { status: 'compliant', checks: [{ label: 'Title length', passed: true }] },
      });
    }

    if (path === '/api/listing-composer/score') {
      return fulfillJson(route, { optimization_score: 91 });
    }

    if (path === '/api/listing-composer/compliance') {
      return fulfillJson(route, { status: 'compliant', checks: [{ label: 'Title length', passed: true }] });
    }

    if (path === '/api/listing-composer/drafts' && method === 'POST') {
      return fulfillJson(route, { id: nextDraftId++ });
    }

    if (path === '/api/listing-composer/drafts' && method === 'GET') {
      const pageNumber = Number(url.searchParams.get('page') || '1');
      return fulfillJson(route, {
        items: [
          {
            id: 101,
            title: 'Retro Dog Mom T-Shirt',
            description: 'A trend-aware shirt for dog moms.',
            tags: ['dog mom', 'summer tee'],
            language: 'en',
            field_order: ['title', 'description', 'tags'],
            updated_at: '2026-04-25T12:00:00.000Z',
            revision_count: 2,
            provenance: { ...provenance, source: 'listingdraft_table' },
          },
        ],
        total: 4,
        page: pageNumber,
        page_size: 3,
        sort_by: 'updated_at',
        sort_order: 'desc',
        provenance: { ...provenance, source: 'listingdraft_table' },
      });
    }

    if (/^\/api\/listing-composer\/drafts\/\d+$/.test(path) && method === 'GET') {
      return fulfillJson(route, {
        id: Number(path.split('/').pop()),
        title: 'Loaded Draft Title',
        description: 'Loaded draft description',
        tags: ['loaded'],
        language: 'en',
        field_order: ['title', 'description', 'tags'],
        provenance: { ...provenance, source: 'listingdraft_table' },
      });
    }

    if (/^\/api\/listing-composer\/drafts\/\d+\/history$/.test(path)) {
      const segments = path.split('/');
      const draftId = Number(segments[segments.length - 2]);
      return fulfillJson(route, [
        {
          id: 301,
          draft_id: draftId,
          title: 'Retro Dog Mom T-Shirt',
          description: 'Revision sourced from listingdraftrevision_table.',
          tags: ['dog mom', 'summer tee'],
          metadata: { product_type: 'T-Shirt' },
          created_at: '2026-04-25T12:00:00.000Z',
          provenance: { ...provenance, source: 'listingdraftrevision_table' },
        },
      ]);
    }

    if (path === '/api/listing-composer/publish-queue') {
      const queuePage = Number(url.searchParams.get('page') || '1');
      const queueStatus = url.searchParams.get('status') || 'queued';
      return fulfillJson(route, {
        items: [
          {
            queue_item_id: 501,
            draft_id: 101,
            status: queueStatus,
            mode: 'implementation_required',
            message: 'Draft is queued locally. Etsy and Printify remain credential-gated and non-blocking.',
            integration_status: {
              etsy: { status: 'needs_implementation', blocking: false },
              printify: { status: 'needs_implementation', blocking: false },
              openai: { status: 'not_required' },
            },
            created_at: '2026-04-25T12:00:00.000Z',
            provenance: { ...provenance, source: 'automationjob_table' },
          },
        ],
        total: 5,
        page: queuePage,
        page_size: 4,
        provenance: { ...provenance, source: 'automationjob_table' },
      });
    }

    if (/^\/api\/listing-composer\/drafts\/\d+\/publish-queue$/.test(path)) {
      const segments = path.split('/');
      const draftId = Number(segments[segments.length - 2]);
      return fulfillJson(route, {
        queue_item_id: 501,
        draft_id: draftId,
        status: 'queued',
        mode: 'implementation_required',
        message: 'Queued locally; live marketplace credentials remain optional for this workflow.',
        integration_status: {
          etsy: { status: 'needs_implementation', blocking: false },
          printify: { status: 'needs_implementation', blocking: false },
          openai: { status: 'not_required', blocking: false },
        },
        created_at: '2026-04-25T12:00:00.000Z',
        provenance: { ...provenance, source: 'automationjob_table' },
      });
    }

    if (/^\/api\/listing-composer\/drafts\/\d+\/export$/.test(path)) {
      const segments = path.split('/');
      return fulfillJson(route, {
        draft_id: Number(segments[segments.length - 2]),
        title: 'Exported Listing',
        description: 'Exported listing description',
        tags: ['dog mom'],
        metadata: { source: 'e2e' },
        score: { optimization_score: 91 },
        compliance: { status: 'compliant' },
        provenance,
      });
    }

    if (path === '/api/ab-tests/dashboard') {
      return fulfillJson(route, abDashboard(abExperiments));
    }

    if (path === '/api/ab-tests/' && method === 'POST') {
      const payload = request.postDataJSON() as Record<string, any>;
      const created = {
        ...baseExperiment,
        id: 12,
        name: payload.name,
        product_id: payload.product_id,
        product: 'Dog Mom Vintage Hoodie',
        experiment_type: payload.experiment_type,
        variants: payload.variants.map((variant: any, index: number) => ({
          id: 120 + index,
          name: variant.name,
          weight: variant.weight,
          impressions: 0,
          clicks: 0,
          ctr: 0,
        })),
      };
      abExperiments = [...abExperiments, created];
      return fulfillJson(route, { id: created.id });
    }

    const abActionMatch = path.match(/^\/api\/ab-tests\/(\d+)\/(pause|duplicate|end|push-winner)$/);
    if (abActionMatch) {
      const id = Number(abActionMatch[1]);
      const action = abActionMatch[2];
      const status = action === 'push-winner' ? 'pushed' : action === 'end' ? 'completed' : action === 'pause' ? 'paused' : 'running';
      abExperiments = abExperiments.map((experiment) =>
        experiment.id === id ? { ...experiment, status } : experiment
      );
      return fulfillJson(route, {
        id,
        status,
        demo_state: true,
        integration_status: { message: action === 'push-winner' ? 'Winner pushed into listing draft state.' : 'Experiment state updated.' },
      });
    }

    if (path === '/api/notifications/dashboard') {
      return fulfillJson(route, notificationsDashboard);
    }

    if (/^\/api\/notifications\/\d+\/read$/.test(path)) {
      return fulfillJson(route, { read_status: true });
    }

    if (path === '/api/notifications/jobs') {
      return fulfillJson(route, { id: 99, status: 'on_track', demo_state: true });
    }

    if (path === '/api/notifications/rules') {
      return fulfillJson(route, { id: 88, active: true, demo_state: true });
    }

    if (/^\/api\/notifications\/rules\/\d+$/.test(path)) {
      return fulfillJson(route, { id: Number(path.split('/').pop()), active: false, demo_state: true });
    }

    if (path === '/api/notifications/preferences') {
      const payload = request.postDataJSON() as Record<string, boolean>;
      return fulfillJson(route, {
        email: { enabled: payload.email_enabled ?? true },
        in_app: { enabled: payload.in_app_enabled ?? true },
        slack: { enabled: false, connected: false, status: 'credentials_missing' },
      });
    }

    if (path === '/api/settings/dashboard') {
      return fulfillJson(route, {
        ...settingsDashboard,
        localization: { ...settingsDashboard.localization, currency: savedCurrency },
      });
    }

    if (path === '/api/settings/localization') {
      const payload = request.postDataJSON() as Record<string, unknown>;
      savedCurrency = String(payload.currency || savedCurrency);
      return fulfillJson(route, {
        saved: true,
        localization: { ...settingsDashboard.localization, ...payload },
      });
    }

    if (path === '/api/settings/brand-profiles') {
      return fulfillJson(route, {
        profile: { id: 2, name: 'New Brand Profile', active: false },
        demo_state: true,
      });
    }

    if (/^\/api\/settings\/brand-profiles\/\d+\/default$/.test(path)) {
      const segments = path.split('/');
      return fulfillJson(route, { profile: { id: Number(segments[segments.length - 2]), active: true } });
    }

    if (path === '/api/settings/usage-ledger') {
      return fulfillJson(route, {
        demo_state: true,
        items: [{ resource_type: 'image_generation', quantity: 25, source: 'e2e_fixture' }],
      });
    }

    if (path === '/api/settings/users/invite') {
      return fulfillJson(route, {
        member: {
          id: 2,
          name: 'New User',
          email: 'new.user@podpusher.com',
          role: 'Viewer',
          permissions: ['Analytics'],
          status: 'pending',
          last_active_at: '2026-04-25T12:00:00.000Z',
        },
      });
    }

    if (/^\/api\/settings\/users\/\d+\/role$/.test(path)) {
      const payload = request.postDataJSON() as Record<string, unknown>;
      return fulfillJson(route, {
        member: { ...settingsDashboard.team_members[0], role: payload.role || 'Editor' },
      });
    }

    if (/^\/api\/settings\/integrations\/[^/]+\/configure$/.test(path)) {
      return fulfillJson(route, {
        demo_state: true,
        message: 'Credential-backed setup is unavailable in local mode.',
      });
    }

    return fulfillJson(route, {});
  });
}

function abDashboard(experiments: JsonValue) {
  return {
    cards: metrics.slice(0, 4),
    experiments,
    product_options: [
      { id: 101, name: 'Retro Beach Sunset Tee' },
      { id: 102, name: 'Dog Mom Vintage Hoodie' },
    ],
    provenance,
  };
}

async function fulfillJson(route: Route, body: JsonValue | Record<string, unknown>) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    headers: corsHeaders(),
    body: JSON.stringify(body),
  });
}

async function fulfillCorsPreflight(route: Route) {
  await route.fulfill({
    status: 204,
    headers: corsHeaders(),
    body: '',
  });
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,OPTIONS',
    'Access-Control-Allow-Headers': 'authorization,content-type,x-user-id',
  };
}
