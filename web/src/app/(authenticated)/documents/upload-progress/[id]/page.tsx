"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { documentService } from "@/services/api/document.service";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, FileText, AlertCircle } from "lucide-react";
import { APP_ROUTES } from "@/lib/constants";

interface Document {
  id: number;
  title: string;
  processing_status: number;
  created_at: string;
  updated_at: string;
  space_id: number;
}

const PROCESSING_STAGES = [
  {
    title: "Upload Complete",
    description: "Your document has been successfully uploaded and is waiting to be processed.",
    icon: <FileText className="h-6 w-6 text-blue-500" />
  },
  {
    title: "Processing Document",
    description: "We're extracting text and analyzing the structure of your document.",
    icon: <Loader2 className="h-6 w-6 text-yellow-500 animate-spin" />
  },
  {
    title: "Analyzing Content",
    description: "Analyzing the content and preparing for knowledge extraction.",
    icon: <Loader2 className="h-6 w-6 text-yellow-500 animate-spin" />
  },
  {
    title: "Generating Insights",
    description: "Creating searchable index and processing final steps.",
    icon: <Loader2 className="h-6 w-6 text-yellow-500 animate-spin" />
  },
  {
    title: "Ready",
    description: "Your document has been fully processed and is ready to use!",
    icon: <CheckCircle2 className="h-6 w-6 text-green-500" />
  }
];

export default function DocumentUploadProgressPage() {
  const router = useRouter();
  const params = useParams();
  const documentId = params?.id as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [progressPercent, setProgressPercent] = useState(0);

  // Calculate progress percentage based on processing status
  const calculateProgress = (status: number) => {
    const totalStages = PROCESSING_STAGES.length;
    const normalizedStatus = Math.min(Math.max(status, 0), totalStages - 1);
    return Math.round(((normalizedStatus + 1) / totalStages) * 100);
  };

  // Fetch document data
  const fetchDocument = async () => {
    try {
      if (!documentId) return;
      
      // If we've already completed, no need to fetch again
      if (document?.processing_status === 4) return;
      
      const response = await documentService.getDocumentById(parseInt(documentId));
      
      if (response?.data?.data) {
        const documentData = response.data.data;
        setDocument(documentData);
        setProgressPercent(calculateProgress(documentData.processing_status));
      } else {
        throw new Error("Failed to fetch document data");
      }
    } catch (error) {
      console.error("Error fetching document:", error);
      setError("Failed to load document progress. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocument();
    
    // Set up polling to check progress
    const intervalId = setInterval(() => {
      fetchDocument();
    }, 5000); // Poll every 5 seconds
    
    return () => clearInterval(intervalId);
  }, [documentId]);

  // Get current stage information
  const getCurrentStage = () => {
    if (!document) return PROCESSING_STAGES[0];
    const status = Math.min(Math.max(document.processing_status, 0), PROCESSING_STAGES.length - 1);
    return PROCESSING_STAGES[status];
  };

  const currentStage = getCurrentStage();
  const isComplete = document?.processing_status === 4;

  if (loading && !document) {
    return (
      <div className="container max-w-3xl mx-auto py-10 px-4">
        <Card className="w-full">
          <CardHeader className="text-center">
            <CardTitle>Loading document information...</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-10">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container max-w-3xl mx-auto py-10 px-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <div className="mt-4 flex justify-center">
          <Button onClick={() => router.push(APP_ROUTES.DASHBOARD)}>
            Return to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-3xl mx-auto py-10 px-4">
      <Card className="w-full">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Document Processing</CardTitle>
          {document?.title && (
            <p className="text-muted-foreground mt-2 text-lg font-medium">
              {document.title}
            </p>
          )}
        </CardHeader>
        
        <CardContent className="space-y-8">
          {/* Progress bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>Progress</span>
              <span>{progressPercent}%</span>
            </div>
            <Progress value={progressPercent} className="h-2" />
          </div>
          
          {/* Current stage */}
          <div className="bg-muted/50 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="mt-1">{currentStage.icon}</div>
              <div className="space-y-1">
                <h3 className="text-lg font-medium">{currentStage.title}</h3>
                <p className="text-muted-foreground">
                  {currentStage.description}
                </p>
              </div>
            </div>
          </div>
          
          {/* Estimated time (optional) */}
          {!isComplete && (
            <p className="text-sm text-center text-muted-foreground">
              This process may take a few minutes depending on the document size.
            </p>
          )}
        </CardContent>
        
        <CardFooter className="flex justify-center gap-4">
          {isComplete ? (
            <>
              <Button 
                onClick={() => router.push(`/documents/${document.id}`)}
                className="gap-2"
              >
                <FileText className="h-4 w-4" />
                View Document
              </Button>
              <Button 
                variant="outline" 
                onClick={() => router.push(`/spaces/${document.space_id}`)}
              >
                Return to Space
              </Button>
            </>
          ) : (
            <Button 
              variant="outline" 
              onClick={() => router.push(`/spaces/${document?.space_id}`)}
            >
              Continue in Background
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
