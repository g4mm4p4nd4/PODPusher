import React, { useEffect, useRef, useState } from 'react';

import { Button, Panel, Pill, ProgressBar } from './ControlCenter';
import {
  DraftData,
  checkListingDraftCompliance,
  fetchTagSuggestions,
  generateListingDraft,
  loadDraft,
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

export default function ListingComposer({ onPublish }: Props) {
  const [activeStep, setActiveStep] = useState(0);
  const [niche, setNiche] = useState('Home Decor Wall Art');
  const [primaryKeyword, setPrimaryKeyword] = useState('Boho Sun Wall Art');
  const [productType, setProductType] = useState('Canvas Print');
  const [tone, setTone] = useState('Warm & Inviting');
  const [targetAudience, setTargetAudience] = useState('Home Decor Enthusiasts');
  const [brandRules, setBrandRules] = useState(
    'Use eco-friendly links, premium materials, and original designs.'
  );
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [suggested, setSuggested] = useState<string[]>([]);
  const [language, setLanguage] = useState('en');
  const [score, setScore] = useState<any>(null);
  const [compliance, setCompliance] = useState<any>(null);
  const [draftStatus, setDraftStatus] = useState('Draft not saved');
  const lastLengthsRef = useRef({ title: 0, description: 0 });

  const isTitleInvalid = title.length > 140;
  const isDescriptionInvalid = description.length > 5000;
  const isFormInvalid = isTitleInvalid || isDescriptionInvalid || !title.trim();

  useEffect(() => {
    const id = localStorage.getItem('draftId');
    if (!id) return;
    loadDraft(Number(id))
      .then((draft: DraftData) => {
        setTitle(draft.title);
        setDescription(draft.description);
        setTags(draft.tags);
        setLanguage(draft.language);
      })
      .catch(() => undefined);
  }, []);

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

  const regenerate = async () => {
    const generated = await generateListingDraft({
      niche,
      primary_keyword: primaryKeyword,
      product_type: productType,
      tone,
      target_audience: targetAudience,
      brand_rules: brandRules,
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

  const save = async () => {
    const id = await saveDraft({
      id: Number(localStorage.getItem('draftId')) || undefined,
      title,
      description,
      tags,
      language,
      field_order: ['product', 'keywords', 'title', 'description', 'tags', 'metadata'],
    });
    localStorage.setItem('draftId', String(id));
    setDraftStatus('Draft saved just now');
    await refreshScore();
  };

  const publish = (event: React.FormEvent) => {
    event.preventDefault();
    if (isFormInvalid) return;
    onPublish?.({ title, description, tags, language, field_order: steps });
  };

  return (
    <form onSubmit={publish} className="space-y-4">
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
        <Panel title="Product Inputs">
          <div className="space-y-3">
            <Field label="Niche" value={niche} onChange={setNiche} />
            <Field label="Primary Keyword" value={primaryKeyword} onChange={setPrimaryKeyword} />
            <SelectField label="Product Type" value={productType} onChange={setProductType} options={['Canvas Print', 'T-Shirt', 'Mug', 'Tote Bag']} />
            <SelectField label="Tone" value={tone} onChange={setTone} options={['Warm & Inviting', 'Humorous, Positive', 'Minimal, Calm']} />
            <SelectField label="Target Audience" value={targetAudience} onChange={setTargetAudience} options={['Home Decor Enthusiasts', 'Dog Lovers', 'Teachers', 'Outdoor Buyers']} />
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
        </div>

        <div className="space-y-4">
          <Panel title="Listing Preview">
            <div className="mb-3 flex aspect-square items-center justify-center rounded-md bg-slate-800 p-4 text-center text-sm text-orange-300">
              {title || 'Generated product preview'}
            </div>
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
              <p>Use lifestyle mockups to boost conversion.</p>
              <p>Add a short video to increase trust.</p>
              <p>Refresh tags weekly as trends shift.</p>
            </div>
          </Panel>
        </div>
      </div>

      <div className="sticky bottom-0 -mx-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 bg-slate-950/95 px-4 py-3">
        <div className="flex gap-2">
          <Button onClick={regenerate}>Regenerate All</Button>
          <Button onClick={save}>Save Draft</Button>
        </div>
        <span className="text-sm text-emerald-400">{draftStatus}</span>
        <div className="flex gap-2">
          <Button type="submit" variant="primary" disabled={isFormInvalid}>Publish Queue</Button>
          <Button>Export</Button>
        </div>
      </div>
    </form>
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
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none"
      >
        {options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </label>
  );
}
