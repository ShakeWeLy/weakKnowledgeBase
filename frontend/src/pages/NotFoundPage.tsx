import { Link } from 'react-router-dom';

import { EmptyBlock } from '../components/common/StateBlock';

export function NotFoundPage() {
  return (
    <div className="w-full p-6">
      <EmptyBlock
        title="页面不存在"
        action={
          <Link to="/knowledge" className="text-sm text-primary underline">
            返回知识探索
          </Link>
        }
      />
    </div>
  );
}
