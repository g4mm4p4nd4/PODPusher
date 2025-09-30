import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { resolveApiUrl } from '../services/apiBase';

interface DesignIdea {
  name: string;
  ideas: string[];
}

export default function DesignIdeas() {
  const { t } = useTranslation('common');
  const [ideas, setIdeas] = useState<DesignIdea[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get<DesignIdea[]>(resolveApiUrl('/design-ideas'));
        setIdeas(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('design.title')}</h1>
      {ideas.map(idea => (
        <div key={idea.name}>
          <h2 className="text-xl font-semibold capitalize">{idea.name}</h2>
          <ul className="list-disc list-inside pl-4">
            {idea.ideas.map(item => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
