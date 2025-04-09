"use client"
import React, { useEffect, useState } from "react";
import { spaceService } from "@/services/api/space.service";
import { useRouter } from "next/navigation";

interface PublicSpace {
  id: number;
  name: string;
  description: string;
  privacy_status: boolean;
  created_at: string;
}

export default function PublicSpacesPage() {
  const [publicSpaces, setPublicSpaces] = useState<PublicSpace[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchPublicSpaces = async () => {
      try {
        const response = await spaceService.getSpacePublic();
        setPublicSpaces(response.public_spaces || []);
      } catch (err) {
        setError("Failed to fetch public spaces");
      } finally {
        setLoading(false);
      }
    };

    fetchPublicSpaces();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-12 px-4 sm:px-6 lg:px-8">
      <h1 className="text-5xl font-extrabold text-center text-gray-900 mb-10">
        <span className="bg-gradient-to-r from-blue-500 to-purple-600 text-transparent bg-clip-text">
          Public Spaces
        </span>
      </h1>
      <p className="text-center text-primary text-lg mb-6">
        Explore a collection of amazing public spaces 🌍
      </p>

      {error ? (
        <p className="text-center text-red-600">{error}</p>
      ) : publicSpaces.length === 0 ? (
        <p className="text-center text-gray-600 text-lg">
          🚫 There is no public space.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {publicSpaces.map((space: PublicSpace) => (
            <div
              key={space.id}
              onClick={() => router.push(`/spaces/${space.id}`)}
              className="bg-primary/1 p-6 rounded-2xl shadow-xl hover:shadow-2xl border transition-all transform hover:scale-105 duration-300"
            >
              <h2 className="text-2xl font-semibold text-foreground hover:text-blue-600 transition-colors">
                {space.name}
              </h2>
              <p className="mt-3 text-primary text-sm">{space.description}</p>
              <div className="mt-6 flex justify-between items-center">
                <span
                  className={`px-4 py-2 text-sm rounded-full ${
                    space.privacy_status
                      ? "bg-red-100 text-red-600 border border-red-300"
                      : "bg-green-100 text-green-600 border border-green-300"
                  }`}
                >
                  {space.privacy_status ? "Private" : "Public"}
                </span>
                <span className="text-sm text-gray-400">
                  {new Date(space.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}