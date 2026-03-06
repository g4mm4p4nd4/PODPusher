import { getCommonStaticProps } from '../utils/translationProps';
import SocialMediaGenerator from '../components/SocialMediaGenerator';

export default function SocialGeneratorPage() {
  return <SocialMediaGenerator />;
}

export const getStaticProps = getCommonStaticProps;
