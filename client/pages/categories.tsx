import { GetServerSideProps } from 'next';
import axios from 'axios';
import { useTranslation } from 'next-i18next';

export type ProductCategory = {
  name: string;
  items: string[];
};

type CategoriesProps = {
  categories: ProductCategory[];
};

export default function Categories({ categories }: CategoriesProps) {
  const { t } = useTranslation('common');
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('categories.title')}</h1>
      {categories.map(cat => (
        <div key={cat.name} className="mb-4">
          <h2 className="text-xl font-semibold capitalize">{cat.name}</h2>
          <ul className="list-disc list-inside pl-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1">
            {cat.items.map(item => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<CategoriesProps> = async () => {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  try {
    const res = await axios.get<ProductCategory[]>(`${api}/product-categories`);
    return { props: { categories: res.data } };
  } catch (err) {
    console.error(err);
    return { props: { categories: [] } };
  }
};
