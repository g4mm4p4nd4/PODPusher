import React from 'react';

import { PageHeader } from '../components/ControlCenter';
import ListingComposer from '../components/ListingComposer';
import { getCommonStaticProps } from '../utils/translationProps';

export default function ListingComposerPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        title="Automated Listing Composer"
        subtitle="Create high-converting Etsy listings in minutes with AI-assisted scoring and compliance checks."
      />
      <ListingComposer />
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
