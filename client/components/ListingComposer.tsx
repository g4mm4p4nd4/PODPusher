import { useRouter } from 'next/router';
import React, { useEffect, useRef, useState } from 'react';

import { Button, Panel, Pill, ProgressBar, ProvenanceNote } from './ControlCenter';
import { DemoProductArt, variantForText } from './DemoProductArt';
import {
  DraftData,
  DraftListResponse,
  DraftRevision,
  PublishQueueListResponse,
  checkListingDraftCompliance,
  exportDraft,
  fetchDraftHistory,
  fetchTagSuggestions,
  generateListingDraft,
  listDrafts,
  listPublishQueue,
  loadDraft,
  queueDraftForPublish,
  saveDraft,
  scoreListingDraft,
} from '../services/listings';

interface Props {
  onPublish?: (data: DraftData) => void;
}

const steps = [
  'Product',
  'Keywords',
  'Title',
  'Description',
  'Tags',
  'Metadata',
  'Review',
];

const defaultDemoDraft = buildDemoListingDraft({
  niche: 'Home Decor Wall Art',
  primaryKeyword: 'Boho Sun Wall Art',
  productType: 'Canvas Print',
  tone: 'Warm & Inviting',
  targetAudience: 'Home Decor Enthusiasts',
  materials: 'Canvas, Pine Wood',
  occasion: 'Housewarming',
  holiday: 'None',
  recipient: 'Home Decor Enthusiast',
  style: 'Boho, Abstract, Modern',
});

export default function ListingComposer({ onPublish }: Props) {
  const router = useRouter();
  const [activeStep, setActiveStep] = useState(0);
  const [niche, setNiche] = useState('Home Decor Wall Art');
  const [primaryKeyword, setPrimaryKeyword] = useState('Boho Sun Wall Art');
  const [productType, setProductType] = useState('Canvas Print');
  const [tone, setTone] = useState('Warm & Inviting');
  const [targetAudience, setTargetAudience] = useState('Home Decor Enthusiasts');
  const [brandRules, setBrandRules] = useState(
    'Use eco-friendly links, premium materials, and original designs.'
  );
  const [title, setTitle] = useState(defaultDemoDraft.title);
  const [description, setDescription] = useState(defaultDemoDraft.description);
  const [tags, setTags] = useState<string[]>(defaultDemoDraft.tags);
  const [suggested, setSuggested] = useState<string[]>(defaultDemoDraft.suggested);
  const [language, setLanguage] = useState('en');
  const [materials, setMaterials] = useState('Canvas, Pine Wood');
  const [occasion, setOccasion] = useState('Housewarming');
  const [holiday, setHoliday] = useState('None');
  const [recipient, setRecipient] = useState('Home Decor Enthusiast');
  const [style, setStyle] = useState('Boho, Abstract, Modern');
  const [score, setScore] = useState<any>(defaultDemoDraft.score);
  const [compliance, setCompliance] = useState<any>(defaultDemoDraft.compliance);
  const [draftStatus, setDraftStatus] = useState('Demo/local draft loaded');
  const [queueStatus, setQueueStatus] = useState('Publish queue idle');
  const [exportStatus, setExportStatus] = useState('Export ready');
  const [draftList, setDraftList] = useState<DraftListResponse | null>(null);
  const [draftListPage, setDraftListPage] = useState(1);
  const [draftHistory, setDraftHistory] = useState<DraftRevision[]>([]);
  const [selectedHistoryDraftId, setSelectedHistoryDraftId] = useState<number | null>(null);
  const [publishQueue, setPublishQueue] = useState<PublishQueueListResponse | null>(null);
  const [publishQueuePage, setPublishQueuePage] = useState(1);
  const [publishQueueFilter, setPublishQueueFilter] = useState('all');
  const [activityStatus, setActivityStatus] = useState('Loading source-backed activity...');
  const lastLengthsRef = useRef({ title: 0, description: 0 });

  const isTitleInvalid = title.length > 140;
  const isDescriptionInvalid = description.length > 5000;
  const isFormInvalid = isTitleInvalid || isDescriptionInvalid || !title.trim();

  const applyDraft = (draft: DraftData) => {
    if (draft.title) setTitle(draft.title);
    if (draft.description) setDescription(draft.description);
    if (draft.tags?.length) setTags(draft.tags);
    setLanguage(draft.language || 'en');
    if (draft.niche) setNiche(draft.niche);
    if (draft.primary_keyword) setPrimaryKeyword(draft.primary_keyword);
    if (draft.product_type) setProductType(draft.product_type);
    if (draft.target_audience) setTargetAudience(draft.target_audience);
    if (draft.materials) setMaterials(draft.materials);
    if (draft.occasion) setOccasion(draft.occasion);
    if (draft.holiday) setHoliday(draft.holiday);
    if (draft.recipient) setRecipient(draft.recipient);
    if (draft.style) setStyle(draft.style);
  };

  const loadHistory = async (draftId: number) => {
    setSelectedHistoryDraftId(draftId);
    const history = await fetchDraftHistory(draftId);
    setDraftHistory(history);
  };

  const refreshDraftActivity = async (page = draftListPage) => {
    const list = await listDrafts({
      page,
      page_size: 3,
      sort_by: 'updated_at',
      sort_order: 'desc',
    });
    setDraftList(list);
    setDraftListPage(list.page);
    if (list.items[0]?.id) {
      await loadHistory(list.items[0].id);
    } else {
      setDraftHistory([]);
      setSelectedHistoryDraftId(null);
    }
    setActivityStatus('Source-backed activity loaded');
  };

  const refreshPublishQueue = async (page = publishQueuePage, status = publishQueueFilter) => {
    const queue = await listPublishQueue({
      page,
      page_size: 4,
      status,
    });
    setPublishQueue(queue);
    setPublishQueuePage(queue.page);
    setActivityStatus('Source-backed activity loaded');
  };

  useEffect(() => {
    const id = localStorage.getItem('draftId');
    if (!id) return;
    loadDraft(Number(id))
      .then((draft: DraftData) => {
        applyDraft(draft);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    Promise.all([
      refreshDraftActivity(1),
      refreshPublishQueue(1, publishQueueFilter),
    ]).catch(() => {
      setActivityStatus('Source-backed activity unavailable');
    });
  }, []);

  useEffect(() => {
    if (!router.isReady) return;
    const queryValue = (name: string) => stringParam(router.query[name]);
    const nextNiche = queryValue('niche');
    const nextKeyword = queryValue('keyword') || queryValue('q');
    const nextProductType = queryValue('product_type') || queryValue('productType');
    const nextAudience = queryValue('audience');
    const nextTags = queryValue('tags');
    const nextTone = queryValue('tone');
    const nextStyle = queryValue('style');
    const nextOccasion = queryValue('occasion');
    const nextHoliday = queryValue('holiday');

    if (nextNiche) setNiche(nextNiche);
    if (nextKeyword) setPrimaryKeyword(nextKeyword);
    if (nextProductType) setProductType(nextProductType);
    if (nextAudience) {
      setTargetAudience(nextAudience);
      setRecipient(nextAudience);
    }
    if (nextTone) setTone(nextTone);
    if (nextStyle) setStyle(nextStyle);
    if (nextOccasion) setOccasion(nextOccasion);
    if (nextHoliday) setHoliday(nextHoliday);
    if (nextTags) {
      setTags(nextTags.split(',').map((tag) => tag.trim()).filter(Boolean).slice(0, 13));
    }
    if (nextNiche || nextKeyword || nextProductType || nextAudience || nextTags) {
      const demo = buildDemoListingDraft({
        niche: nextNiche || niche,
        primaryKeyword: nextKeyword || primaryKeyword,
        productType: nextProductType || productType,
        tone: nextTone || tone,
        targetAudience: nextAudience || targetAudience,
        materials,
        occasion: nextOccasion || occasion,
        holiday: nextHoliday || holiday,
        recipient: nextAudience || recipient,
        style: nextStyle || style,
        incomingTags: nextTags,
      });
      setTitle((current) => (current === defaultDemoDraft.title ? demo.title : current));
      setDescription((current) => (current === defaultDemoDraft.description ? demo.description : current));
      setSuggested(demo.suggested);
      setScore(demo.score);
      setCompliance(demo.compliance);
      setDraftStatus(`Prefilled from ${queryValue('source') || 'handoff'}`);
    }
  }, [router.isReady, router.query]);

  useEffect(() => {
    const handler = setTimeout(() => {
      const { title: lastTitle, description: lastDescription } = lastLengthsRef.current;
      if (
        Math.abs(title.length - lastTitle) >= 10 ||
        Math.abs(description.length - lastDescription) >= 10
      ) {
        lastLengthsRef.current = { title: title.length, description: description.length };
        fetchTagSuggestions(title, description)
          .then((items) => setSuggested(items))
          .catch(() => undefined);
      }
    }, 500);
    return () => clearTimeout(handler);
  }, [title, description]);

  useEffect(() => {
    if (!title.trim()) return;
    const handler = setTimeout(() => {
      refreshScore().catch(() => undefined);
    }, 900);
    return () => clearTimeout(handler);
  }, [title, description, tags, primaryKeyword]);

  const regenerate = async () => {
    const generated = await generateListingDraft({
      niche,
      primary_keyword: primaryKeyword,
      product_type: productType,
      tone,
      target_audience: targetAudience,
      brand_rules: brandRules,
      metadata: { materials, occasion, holiday, recipient, style },
    });
    setTitle(generated.title);
    setDescription(generated.description);
    setTags(generated.tags || []);
    setScore(generated.score);
    setCompliance(generated.compliance);
    setActiveStep(2);
  };

  const getSuggestions = async () => {
    lastLengthsRef.current = { title: title.length, description: description.length };
    setSuggested(await fetchTagSuggestions(title, description));
  };

  const refreshScore = async () => {
    const payload = { title, description, tags, primary_keyword: primaryKeyword };
    const [nextScore, nextCompliance] = await Promise.all([
      scoreListingDraft(payload),
      checkListingDraftCompliance(payload),
    ]);
    setScore(nextScore);
    setCompliance(nextCompliance);
  };

  const toggleTag = (tag: string) => {
    if (tags.includes(tag)) {
      setTags(tags.filter((item) => item !== tag));
    } else if (tags.length < 13) {
      setTags([...tags, tag]);
    }
  };

  const persistDraft = async () => {
    const id = await saveDraft({
      id: Number(localStorage.getItem('draftId')) || undefined,
      title,
      description,
      tags,
      language,
      niche,
      primary_keyword: primaryKeyword,
      product_type: productType,
      target_audience: targetAudience,
      materials,
      occasion,
      holiday,
      recipient,
      style,
      field_order: ['product', 'keywords', 'title', 'description', 'tags', 'metadata'],
    });
    localStorage.setItem('draftId', String(id));
    setDraftStatus('Draft saved just now');
    await refreshDraftActivity(1).catch(() => {
      setActivityStatus('Draft saved; source-backed activity refresh failed');
    });
    await refreshScore();
    return id;
  };

  const save = async () => {
    await persistDraft();
  };

  const publish = async () => {
    if (isFormInvalid) return;
    setQueueStatus('Queue pending...');
    try {
      const id = await persistDraft();
      const queued = await queueDraftForPublish(id);
      setQueueStatus(`Queue ${queued.status}: draft ${queued.draft_id}, job ${queued.queue_item_id}`);
      await refreshPublishQueue(1, publishQueueFilter).catch(() => {
        setActivityStatus('Queue updated; source-backed activity refresh failed');
      });
      onPublish?.({
        id,
        title,
        description,
        tags,
        language,
        niche,
        primary_keyword: primaryKeyword,
        product_type: productType,
        target_audience: targetAudience,
        materials,
        occasion,
        holiday,
        recipient,
        style,
        field_order: steps,
      });
    } catch {
      setQueueStatus('Queue error: draft was not queued');
    }
  };

  const exportCurrentDraft = async () => {
    if (isFormInvalid) return;
    setExportStatus('Export pending...');
    try {
      const id = await persistDraft();
      const payload = await exportDraft(id, 'json');
      downloadExportPayload(id, payload);
      setExportStatus(`Export ready: draft ${id}`);
    } catch {
      setExportStatus('Export error: draft was not exported');
    }
  };

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void publish();
      }}
      className="space-y-4"
    >
      <div className="grid gap-3 xl:grid-cols-7">
        {steps.map((step, index) => (
          <button
            key={step}
            type="button"
            onClick={() => setActiveStep(index)}
            className={`rounded-md border px-3 py-2 text-left text-sm ${
              activeStep === index
                ? 'border-orange-500 bg-orange-500/15 text-orange-200'
                : 'border-slate-800 bg-slate-900 text-slate-400'
            }`}
          >
            <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full border border-current text-xs">
              {index + 1}
            </span>
            {step}
          </button>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.75fr_1.6fr_0.95fr]">
        <div className="space-y-4">
          <Panel title="Product Inputs">
            <div className="space-y-3">
              <div className="rounded-md border border-blue-500/30 bg-blue-950/30 p-3 text-xs text-blue-100">
                Default copy and thumbnails are local demo evidence. Live Etsy, Printify, OpenAI, and marketplace generation stay non-blocking until credentials are connected.
              </div>
              <Field label="Niche" value={niche} onChange={setNiche} />
              <Field label="Primary Keyword" value={primaryKeyword} onChange={setPrimaryKeyword} />
              <SelectField label="Product Type" value={productType} onChange={setProductType} options={withCurrent(productType, ['Canvas Print', 'T-Shirt', 'Mug', 'Tote Bag', 'Apparel', 'Drinkware', 'Bags'])} />
              <SelectField label="Tone" value={tone} onChange={setTone} options={['Warm & Inviting', 'Humorous, Positive', 'Minimal, Calm']} />
              <SelectField label="Target Audience" value={targetAudience} onChange={setTargetAudience} options={withCurrent(targetAudience, ['Home Decor Enthusiasts', 'Dog Lovers', 'Teachers', 'Outdoor Buyers', 'Marketplace Buyers'])} />
              <SelectField label="Language" value={language} onChange={setLanguage} options={['en', 'es']} />
              <label className="block text-sm text-slate-300">
                Brand Rules
                <textarea
                  value={brandRules}
                  onChange={(event) => setBrandRules(event.target.value)}
                  maxLength={500}
                  className="mt-1 h-24 w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none"
                />
                <span className="mt-1 block text-xs text-slate-500">{brandRules.length}/500</span>
              </label>
              <Button onClick={regenerate} variant="primary">Auto-Fill from Niche</Button>
            </div>
          </Panel>

          <DraftHistoryPanel
            draftList={draftList}
            draftHistory={draftHistory}
            selectedHistoryDraftId={selectedHistoryDraftId}
            activityStatus={activityStatus}
            onLoadDraft={async (draftId) => {
              const draft = await loadDraft(draftId);
              applyDraft(draft);
              localStorage.setItem('draftId', String(draftId));
              setDraftStatus(`Loaded draft ${draftId}`);
              await loadHistory(draftId);
            }}
            onShowHistory={(draftId) => {
              void loadHistory(draftId).catch(() => {
                setActivityStatus('Draft history unavailable');
              });
            }}
            onPreviousPage={() => {
              const nextPage = Math.max(1, draftListPage - 1);
              void refreshDraftActivity(nextPage).catch(() => {
                setActivityStatus('Draft history unavailable');
              });
            }}
            onNextPage={() => {
              const nextPage = draftListPage + 1;
              void refreshDraftActivity(nextPage).catch(() => {
                setActivityStatus('Draft history unavailable');
              });
            }}
          />
        </div>

        <div className="space-y-4">
          <Panel title="Generated Title" action={<Button onClick={regenerate}>Regenerate</Button>}>
            <label className={`block text-sm font-medium ${isTitleInvalid ? 'text-red-400' : 'text-slate-300'}`} htmlFor="listing-title">
              Title ({title.length}/140)
            </label>
            <input
              id="listing-title"
              aria-label="Title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className={`mt-2 w-full rounded-md border bg-slate-950 p-3 text-sm text-slate-100 outline-none ${
                isTitleInvalid ? 'border-red-500' : 'border-slate-800'
              }`}
              aria-invalid={isTitleInvalid}
            />
            {score ? (
              <div className="mt-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Optimization Score</span>
                  <span>{score.optimization_score}/100</span>
                </div>
                <ProgressBar value={score.optimization_score} tone="green" />
              </div>
            ) : null}
          </Panel>

          <Panel title="Generated Description" action={<Button onClick={regenerate}>Regenerate</Button>}>
            <label className={`block text-sm font-medium ${isDescriptionInvalid ? 'text-red-400' : 'text-slate-300'}`} htmlFor="listing-description">
              Description ({description.length}/5000)
            </label>
            <textarea
              id="listing-description"
              aria-label="Description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className={`mt-2 h-56 w-full rounded-md border bg-slate-950 p-3 text-sm text-slate-100 outline-none ${
                isDescriptionInvalid ? 'border-red-500' : 'border-slate-800'
              }`}
              aria-invalid={isDescriptionInvalid}
            />
          </Panel>

          <Panel title={`Tags (${tags.length}/13)`} action={<Button onClick={getSuggestions}>Suggest Tags</Button>}>
            <div className="mb-3 flex flex-wrap gap-2">
              {tags.map((tag) => (
                <button
                  type="button"
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
                >
                  {tag}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              {suggested.map((tag) => (
                <button
                  type="button"
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`rounded-md border px-2 py-1 text-xs ${
                    tags.includes(tag)
                      ? 'border-orange-500 bg-orange-500 text-white'
                      : 'border-slate-700 bg-slate-950 text-slate-300'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="Metadata">
            <div className="grid gap-3 md:grid-cols-2">
              <SelectField label="Materials" value={materials} onChange={setMaterials} options={withCurrent(materials, ['Canvas, Pine Wood', 'Cotton', 'Ceramic', 'Recycled Polyester'])} />
              <SelectField label="Occasion" value={occasion} onChange={setOccasion} options={withCurrent(occasion, ['Housewarming', 'Birthday', 'Mother\'s Day', 'Graduation', 'Everyday'])} />
              <SelectField label="Holiday" value={holiday} onChange={setHoliday} options={withCurrent(holiday, ['None', 'Christmas', 'Halloween', 'Valentine\'s Day', 'Mother\'s Day'])} />
              <SelectField label="Recipient" value={recipient} onChange={setRecipient} options={withCurrent(recipient, ['Home Decor Enthusiast', 'Dog Lovers', 'Teachers', 'Outdoor Buyers', 'Mom', 'Dad'])} />
              <div className="md:col-span-2">
                <SelectField label="Style" value={style} onChange={setStyle} options={withCurrent(style, ['Boho, Abstract, Modern', 'Vintage Badge', 'Minimal Line Art', 'Retro Summer'])} />
              </div>
            </div>
          </Panel>
        </div>

        <div className="space-y-4">
          <Panel title="Listing Preview">
            <DemoProductArt
              title={title || primaryKeyword}
              subtitle={`${productType} preview - ${niche}`}
              productType={productType}
              variant={variantForText(`${title} ${primaryKeyword} ${style}`)}
              className="mb-3"
            />
            <h3 className="text-lg font-semibold text-slate-50">{title || 'Untitled listing'}</h3>
            <p className="mt-2 text-2xl font-semibold">$34.99+</p>
            <p className="text-sm text-slate-500">Free shipping eligible</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {tags.slice(0, 4).map((tag) => <Pill key={tag}>{tag}</Pill>)}
            </div>
          </Panel>

          <Panel title="Marketplace Compliance">
            {compliance ? (
              <div className="space-y-2">
                <Pill tone={compliance.status === 'compliant' ? 'green' : 'red'}>{compliance.status}</Pill>
                {compliance.checks.map((check: any) => (
                  <div key={check.label} className="flex justify-between gap-2 text-sm">
                    <span className={check.passed ? 'text-slate-300' : 'text-red-300'}>{check.label}</span>
                    <span>{check.passed ? 'Pass' : 'Review'}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Save or score the draft to run local compliance checks.</p>
            )}
          </Panel>

          <Panel title="Quick Tips">
            <div className="space-y-3 text-sm text-slate-400">
              <p className="text-blue-200">Preview source: local demo thumbnail, confidence 72%, updated on first paint.</p>
              <p>Use lifestyle mockups to boost conversion.</p>
              <p>Add a short video to increase trust.</p>
              <p>Refresh tags weekly as trends shift.</p>
            </div>
          </Panel>

          <PublishQueuePanel
            publishQueue={publishQueue}
            filter={publishQueueFilter}
            onFilterChange={(nextFilter) => {
              setPublishQueueFilter(nextFilter);
              void refreshPublishQueue(1, nextFilter).catch(() => {
                setActivityStatus('Publish queue unavailable');
              });
            }}
            onPreviousPage={() => {
              const nextPage = Math.max(1, publishQueuePage - 1);
              void refreshPublishQueue(nextPage, publishQueueFilter).catch(() => {
                setActivityStatus('Publish queue unavailable');
              });
            }}
            onNextPage={() => {
              const nextPage = publishQueuePage + 1;
              void refreshPublishQueue(nextPage, publishQueueFilter).catch(() => {
                setActivityStatus('Publish queue unavailable');
              });
            }}
          />
        </div>
      </div>

      <div className="sticky bottom-0 -mx-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 bg-slate-950/95 px-4 py-3">
        <div className="flex gap-2">
          <Button onClick={regenerate}>Regenerate All</Button>
          <Button onClick={save}>Save Draft</Button>
        </div>
        <div className="space-y-1 text-sm">
          <p className="text-emerald-400">{draftStatus}</p>
          <p className={queueStatus.includes('error') ? 'text-red-300' : 'text-slate-400'}>{queueStatus}</p>
          <p className={exportStatus.includes('error') ? 'text-red-300' : 'text-slate-400'}>{exportStatus}</p>
        </div>
        <div className="flex gap-2">
          <Button type="submit" variant="primary" disabled={isFormInvalid}>Publish Queue</Button>
          <Button onClick={exportCurrentDraft} disabled={isFormInvalid}>Export</Button>
        </div>
      </div>
    </form>
  );
}

function DraftHistoryPanel({
  draftList,
  draftHistory,
  selectedHistoryDraftId,
  activityStatus,
  onLoadDraft,
  onShowHistory,
  onPreviousPage,
  onNextPage,
}: {
  draftList: DraftListResponse | null;
  draftHistory: DraftRevision[];
  selectedHistoryDraftId: number | null;
  activityStatus: string;
  onLoadDraft: (draftId: number) => void | Promise<void>;
  onShowHistory: (draftId: number) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
}) {
  const page = draftList?.page || 1;
  const pageSize = draftList?.page_size || 3;
  const total = draftList?.total || 0;
  const hasPrevious = page > 1;
  const hasNext = page * pageSize < total;

  return (
    <Panel title="Draft History">
      <div className="space-y-3">
        <p className="text-xs text-slate-500">{activityStatus}</p>
        {draftList?.items.length ? (
          <div className="divide-y divide-slate-800 rounded-md border border-slate-800">
            {draftList.items.map((draft) => (
              <div key={draft.id} className="space-y-2 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-100">{draft.title || 'Untitled draft'}</p>
                    <p className="text-xs text-slate-500">
                      {draft.revision_count || 0} revisions / updated {formatDate(draft.updated_at)}
                    </p>
                  </div>
                  <Pill tone={draft.provenance?.is_estimated ? 'orange' : 'green'}>
                    {draft.provenance?.is_estimated ? 'Est' : 'Live'}
                  </Pill>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => draft.id && void onLoadDraft(draft.id)}
                    className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-100"
                  >
                    Load Draft {draft.id}
                  </button>
                  <button
                    type="button"
                    onClick={() => draft.id && onShowHistory(draft.id)}
                    className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-300"
                  >
                    Show History
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="rounded-md border border-slate-800 p-3 text-sm text-slate-500">
            No persisted drafts yet.
          </p>
        )}

        <div className="flex items-center justify-between gap-2 text-xs text-slate-400">
          <span>
            Page {page} / {Math.max(1, Math.ceil(total / pageSize))}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onPreviousPage}
              disabled={!hasPrevious}
              className="rounded-md border border-slate-700 px-2 py-1 disabled:opacity-40"
            >
              Previous Drafts
            </button>
            <button
              type="button"
              onClick={onNextPage}
              disabled={!hasNext}
              className="rounded-md border border-slate-700 px-2 py-1 disabled:opacity-40"
            >
              Next Drafts
            </button>
          </div>
        </div>

        {selectedHistoryDraftId ? (
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-300">Revision trail for draft {selectedHistoryDraftId}</p>
            {draftHistory.length ? (
              <div className="max-h-56 space-y-2 overflow-y-auto pr-1">
                {draftHistory.map((revision) => (
                  <div key={revision.id} className="rounded-md border border-slate-800 p-2 text-xs">
                    <div className="flex items-start justify-between gap-2">
                      <p className="truncate font-medium text-slate-200">{revision.title}</p>
                      <span className="shrink-0 text-slate-500">{formatDate(revision.created_at)}</span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-slate-500">{revision.description}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {revision.tags.slice(0, 4).map((tag) => (
                        <span key={tag} className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <ProvenanceNote provenance={revision.provenance} />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No revisions recorded for this draft.</p>
            )}
          </div>
        ) : null}

        <ProvenanceNote provenance={draftList?.provenance} />
      </div>
    </Panel>
  );
}

function PublishQueuePanel({
  publishQueue,
  filter,
  onFilterChange,
  onPreviousPage,
  onNextPage,
}: {
  publishQueue: PublishQueueListResponse | null;
  filter: string;
  onFilterChange: (value: string) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
}) {
  const page = publishQueue?.page || 1;
  const pageSize = publishQueue?.page_size || 4;
  const total = publishQueue?.total || 0;
  const hasPrevious = page > 1;
  const hasNext = page * pageSize < total;

  return (
    <Panel title="Publish Queue">
      <div className="space-y-3">
        <label className="block text-xs text-slate-400">
          Queue Status
          <select
            aria-label="Queue Status"
            value={filter}
            onChange={(event) => onFilterChange(event.target.value)}
            className="mt-1 w-full rounded-md border border-slate-800 bg-slate-950 p-2 text-sm text-slate-100 outline-none"
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="queued">Queued</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </label>

        {publishQueue?.items.length ? (
          <div className="divide-y divide-slate-800 rounded-md border border-slate-800">
            {publishQueue.items.map((item) => (
              <div key={item.queue_item_id} className="space-y-2 p-3 text-sm">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-slate-100">Draft {item.draft_id}</p>
                    <p className="text-xs text-slate-500">Job {item.queue_item_id} / {formatDate(item.created_at)}</p>
                  </div>
                  <Pill tone={item.status === 'failed' ? 'red' : 'green'}>{item.status}</Pill>
                </div>
                <p className="text-xs text-slate-400">{item.message}</p>
                <p className="text-xs text-blue-200">{summarizeIntegrationStatus(item.integration_status)}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="rounded-md border border-slate-800 p-3 text-sm text-slate-500">
            No queued publish jobs for this filter.
          </p>
        )}

        <div className="flex items-center justify-between gap-2 text-xs text-slate-400">
          <span>
            Page {page} / {Math.max(1, Math.ceil(total / pageSize))}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onPreviousPage}
              disabled={!hasPrevious}
              className="rounded-md border border-slate-700 px-2 py-1 disabled:opacity-40"
            >
              Previous Jobs
            </button>
            <button
              type="button"
              onClick={onNextPage}
              disabled={!hasNext}
              className="rounded-md border border-slate-700 px-2 py-1 disabled:opacity-40"
            >
              Next Jobs
            </button>
          </div>
        </div>

        <ProvenanceNote provenance={publishQueue?.provenance} />
      </div>
    </Panel>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-sm text-slate-300">
      {label}
      <input
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none"
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="block text-sm text-slate-300">
      {label}
      <select
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none"
      >
        {options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </label>
  );
}

function stringParam(value: string | string[] | undefined) {
  if (Array.isArray(value)) return value[0] || '';
  return value || '';
}

function withCurrent(current: string, options: string[]) {
  return options.includes(current) ? options : [current, ...options].filter(Boolean);
}

function formatDate(value?: string) {
  if (!value) return 'unknown';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function summarizeIntegrationStatus(status: Record<string, unknown>) {
  const entries = Object.entries(status || {});
  if (!entries.length) return 'Live marketplace publish still needs implementation/configuration.';
  return entries
    .map(([provider, value]) => {
      if (value && typeof value === 'object' && 'status' in value) {
        return `${provider}: ${String((value as { status?: unknown }).status)}`;
      }
      return `${provider}: ${String(value)}`;
    })
    .join(' / ');
}

function buildDemoListingDraft({
  niche,
  primaryKeyword,
  productType,
  tone,
  targetAudience,
  materials,
  occasion,
  holiday,
  recipient,
  style,
  incomingTags,
}: {
  niche: string;
  primaryKeyword: string;
  productType: string;
  tone: string;
  targetAudience: string;
  materials: string;
  occasion: string;
  holiday: string;
  recipient: string;
  style: string;
  incomingTags?: string;
}) {
  const baseTags = [
    primaryKeyword,
    niche,
    productType,
    occasion,
    holiday !== 'None' ? holiday : '',
    recipient,
    style.split(',')[0],
    'gift idea',
    'wall decor',
    'made to order',
    'local demo',
  ]
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean);
  const tags = (incomingTags ? incomingTags.split(',') : baseTags)
    .map((tag) => tag.trim())
    .filter(Boolean)
    .slice(0, 13);
  const uniqueTags = Array.from(new Set(tags));

  return {
    title: `${primaryKeyword} ${productType} for ${targetAudience}`,
    description: [
      `Bring a ${tone.toLowerCase()} look to your shop with this ${productType.toLowerCase()} concept built around ${primaryKeyword}.`,
      `The demo draft is tuned for ${niche}, ${occasion.toLowerCase()} gifting, and ${style.toLowerCase()} styling.`,
      `Materials: ${materials}. Recipient: ${recipient}. This first-paint copy is generated locally for UI review and can be replaced by credential-backed generation when providers are connected.`,
    ].join('\n\n'),
    tags: uniqueTags,
    suggested: ['etsy seo', 'print on demand', 'seasonal gift', 'shop launch', 'wall art gift'].filter(
      (tag) => !uniqueTags.includes(tag)
    ),
    score: {
      optimization_score: 84,
      seo_score: 82,
      checks: {
        title_length: true,
        tag_count: true,
        keyword_in_title: true,
      },
      provenance: {
        source: 'local_demo_first_paint',
        is_estimated: true,
        updated_at: '2026-04-26T00:00:00Z',
        confidence: 0.72,
      },
    },
    compliance: {
      status: 'compliant',
      checks: [
        { label: 'No restricted credential-backed marketplace action', passed: true },
        { label: 'Local demo copy is labeled', passed: true },
        { label: 'Title within Etsy limit', passed: true },
      ],
    },
  };
}

function downloadExportPayload(draftId: number, payload: unknown) {
  if (
    typeof window === 'undefined' ||
    typeof document === 'undefined' ||
    typeof URL.createObjectURL !== 'function'
  ) {
    return;
  }
  const body = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
  const blob = new Blob([body], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `listing-draft-${draftId}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}
