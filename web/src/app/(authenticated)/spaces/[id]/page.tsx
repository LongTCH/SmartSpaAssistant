'use client';
import React, { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { spaceService } from '@/services/api/space.service';
import {
  FaEdit,
  FaTrash,
  FaEye,
  FaFilePdf,
  FaRobot,
} from 'react-icons/fa';
import { Button } from '@/components/ui/button';
import { SearchBar } from '@/components/ui/search-bar';
import { Bot } from 'lucide-react';
import ImportModal from './components/ImportModal';

interface Document {
  id: number;
  name: string;
  s3_url: string;
  privacy_status: boolean;
  created_at: string;
}

interface Space {
  id: number;
  name: string;
  description: string;
  privacy_status: boolean;
  created_at: string;
}

export default function SpaceDetailPage() {
  const [space, setSpace] = useState<Space | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [currentPage, setCurrentPage] = useState<number>(1);
  const itemsPerPage = 5;

  const pathname = usePathname();
  const spaceId = pathname?.split('/')[2];

  useEffect(() => {
    if (!spaceId) return;

    const fetchSpaceDetail = async () => {
      try {
        const spaceResponse = await spaceService.getSpaceById(spaceId);
        setSpace(spaceResponse);
        const documentsResponse = await spaceService.getDocumentBySpace(
          spaceId
        );
        setDocuments(documentsResponse.documents);
      } catch (err) {
        setError('Failed to fetch space details');
      } finally {
        setLoading(false);
      }
    };

    fetchSpaceDetail();
  }, [spaceId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-2xl font-semibold text-gray-800">Loading...</p>
      </div>
    );
  }

  const totalPages = Math.ceil(documents.length / itemsPerPage);
  const paginatedDocuments = documents.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  if(!space) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] text-center px-4">
        <Bot className="h-16 w-16 text-muted-foreground mb-4 animate-bounce" />
        <h1 className="text-3xl font-bold mb-2">Oops! Space not found</h1>
        <p className="text-muted-foreground mb-6">
          {"We couldn't find the space you're looking for."}
        </p>
        <Button variant="default" onClick={() => window.history.back()}>
          ← Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto relative">
        <h1 className="text-4xl font-extrabold text-center text-primary">
          {space?.name}
        </h1>
        <p className="text-center text-lg text-primary">{space?.description}</p>
        <div className="bg-background rounded-xl shadow-lg p-6 md:p-10 space-y-6">
          <div className="flex items-center justify-between w-full mb-4">
            <div className="flex">
              <SearchBar onSearch={(query) => console.log(query)} />
            </div>
            <div className="flex gap-4">
              <ImportModal spaceId={spaceId}/>
              <Button className="flex items-center gap-2">
                <FaRobot size={22} />
                Open Chat
              </Button>
            </div>
          </div>

          <div className="mt-6">
            {documents.length === 0 ? (
              <p className="text-center text-gray-500 italic">
                No documents uploaded yet.
              </p>
            ) : (
              <ul className="space-y-4 max-h-[calc(100vh-100px)] overflow-y-auto">
                {paginatedDocuments.map((document) => (
                  <li
                    key={document.id}
                    className="border hover:bg-accent hover:text-accent-foreground rounded-lg p-5 flex justify-between items-center shadow-sm hover:shadow-md transition-all duration-300"
                  >
                    <div className="flex items-center space-x-3">
                      <FaFilePdf className="text-red-500 text-2xl" />
                      <div>
                        <h3 className="text-lg font-semibold text-primary">
                          {document.name}
                        </h3>
                        <p className="text-xs text-primary">
                          Uploaded:{' '}
                          {new Date(document.created_at).toLocaleDateString()}
                        </p>
                        <span
                          className={`inline-block px-3 py-1 mt-2 text-xs font-medium rounded-full ${
                            document.privacy_status
                              ? 'bg-red-100 text-red-600'
                              : 'bg-green-100 text-green-600'
                          }`}
                        >
                          {document.privacy_status ? 'Private' : 'Public'}
                        </span>
                      </div>
                    </div>

                    <div className="flex space-x-3">
                      <a
                        href={document.s3_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Button variant="outline">
                          <FaEye size={18} />
                        </Button>
                      </a>
                      <Button variant="outline">
                        <FaEdit size={18} />
                      </Button>
                      <Button variant="destructive">
                        <FaTrash size={18} />
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        {totalPages > 1 && (
          <div className="flex justify-center mt-6 space-x-3">
            <Button
              variant="outline"
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg text-primary transition-all disabled:opacity-50"
            >
              Prev
            </Button>
            <span className="text-primary font-semibold">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="outline"
              onClick={() =>
                setCurrentPage((prev) => Math.min(prev + 1, totalPages))
              }
              disabled={currentPage === totalPages}
              className="px-4 py-2 border border-gray-300 rounded-lg text-primary transition-all disabled:opacity-50"
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
