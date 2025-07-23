import axios from 'axios';
import { useState } from 'react';

export default function Generate() {
  const [term, setTerm] = useState('');
  const [result, setResult] = useState<any>(null);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);
    try {
      const res = await axios.post(`${api}/generate`, { term });
      setResult(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-2">Generate Product Idea</h1>
      <form onSubmit={submit} className="flex gap-2">
        <input
          type="text"
          className="border p-2 flex-grow"
          placeholder="Enter trend term"
          value={term}
          onChange={e => setTerm(e.target.value)}
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          Generate
        </button>
      </form>
      {result && (
        <div className="bg-gray-100 p-4 rounded">
          <pre className="whitespace-pre-wrap text-sm">
{JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
