'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useRouter } from 'next/navigation';
import { spaceService } from '@/services/api/space.service';
import { toast, Toaster } from 'sonner';
import { APP_ROUTES } from '@/lib/constants';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function CreateSpacePage() {
  const router = useRouter();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [loading, setLoading] = useState(false);

  const [nameError, setNameError] = useState('');
  const [descriptionError, setDescriptionError] = useState('');

  const handleCreateSpace = async () => {
    let hasError = false;

    setNameError('');
    setDescriptionError('');

    if (!name.trim()) {
      setNameError('Please enter space name');
      hasError = true;
    }

    if (!description.trim()) {
      setDescriptionError('Please enter space description');
      hasError = true;
    }

    if (hasError) return;

    setLoading(true);
    try {
      const payload = {
        name,
        description,
        privacy_status: isPrivate,
      };

      await spaceService.createSpace(payload);
      toast.success('Create space successfully!');
      router.push(APP_ROUTES.SPACES.MINE);
    } catch (error) {
      toast.error('Create Space failed!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Toaster position="top-right" richColors style={{ zIndex: 9999 }} />
      <Card className="w-full max-w-xl shadow-xl rounded-2xl border border-primary/1 bg-primary/1">
        <CardHeader>
          <CardTitle className="text-5xl font-extrabold text-center text-gray-900 mb-10">
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 text-transparent bg-clip-text">
              Create New Space
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label htmlFor="name" className="mb-4">
              Space Name
            </Label>
            <Input
              id="name"
              placeholder="Enter the space name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            {nameError && (
              <p className="text-sm text-red-500 mt-1">{nameError}</p>
            )}
          </div>

          <div>
            <Label htmlFor="description" className="mb-4">
              Description
            </Label>
            <Textarea
              id="description"
              placeholder="Enter a description for the space"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            {descriptionError && (
              <p className="text-sm text-red-500 mt-1">{descriptionError}</p>
            )}
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="privacy">Private</Label>
            <Switch
              id="privacy"
              checked={isPrivate}
              onCheckedChange={setIsPrivate}
            />
          </div>

          <Button
            className="w-full"
            onClick={handleCreateSpace}
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Space'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
