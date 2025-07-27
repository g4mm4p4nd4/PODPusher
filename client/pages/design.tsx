import { GetServerSideProps } from 'next';
import axios from 'axios';
import { useTranslation } from 'next-i18next';

export type DesignIdea = {
  name: string;
  ideas: string[];
};

type DesignProps = {
  designs: DesignIdea[];
};

export default function Design({ designs }: DesignProps) {
  const { t } = useTranslation('common');
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('design.title')}</h1>
      {designs.map(d => (
        <div key={d.name} className="mb-4">
          <h2 className="text-xl font-semibold capitalize">
            {d.name.replace(/_/g, ' ')}
          </h2>
          <ul className="list-disc list-inside pl-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1">
            {d.ideas.map(idea => (
              <li key={idea}>{idea}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<DesignProps> = async () => {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  try {
    const res = await axios.get<DesignIdea[]>(`${api}/design-ideas`);
    return { props: { designs: res.data } };
  } catch (err) {
    console.error(err);
    return { props: { designs: [] } };
  }
};
