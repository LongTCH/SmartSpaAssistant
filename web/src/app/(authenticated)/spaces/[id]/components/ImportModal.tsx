"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogHeader, DialogTitle, DialogContent, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import apiClient from "@/lib/axios";
import { useForm } from "react-hook-form";
import { FaPlus } from "react-icons/fa";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, AlertCircle } from "lucide-react";
import { documentService } from "@/services/api/document.service";
import { useRouter } from "next/navigation";
import { APP_ROUTES } from "@/lib/constants";

interface ImportDialogProps {
    spaceId: string;
}

export default function ImportDialog(props: ImportDialogProps) {
    const { spaceId } = props;
    const [isUploading, setIsUploading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const router = useRouter();
    
    const [feedback, setFeedback] = useState<{
        type: 'success' | 'error' | null;
        message: string;
    }>({ type: null, message: '' });
    
    const form = useForm({
        defaultValues: {
            file: undefined as unknown as FileList,
        }
    });

    const handleFileUpload = async (data: { file: FileList }) => {
        try {
            setFeedback({ type: null, message: '' });
            setIsUploading(true);
            
            const file = data.file?.[0];
            
            if (!file) {
                setFeedback({
                    type: 'error',
                    message: 'Please select a file to upload.'
                });
                setIsUploading(false);
                return;
            }

            const response = await documentService.uploadDocumet(parseInt(spaceId), file);
            
            if (response.data.status === 200 || response.data.status === 201) {
                setFeedback({
                    type: 'success',
                    message: response.data.message || 'Document uploaded successfully.'
                });
                
                form.reset();

                const document = response.data.data.document;
                const docId = document.id
                
                setTimeout(() => {
                    setIsOpen(false);
                    setFeedback({ type: null, message: '' });
                    router.push(APP_ROUTES.DOCUMENT.UPLOAD_PROGRESS(docId));
                }, 1000);
            } else {
                throw new Error(response.data.message || "Failed to upload document");
            }
        } catch (error: any) {
            console.error("Document upload error:", error);
            
            let errorMessage = "Failed to upload document. Please try again.";
            
            // Extract error message from different possible error objects
            if (error.response?.data) {
                errorMessage = error.response.data.message || 
                              error.response.data.error || 
                              errorMessage;
            } else if (error instanceof Error) {
                errorMessage = error.message;
            }
            
            setFeedback({
                type: 'error',
                message: errorMessage
            });
        } finally {
            setIsUploading(false);
        }
    };

    // Reset feedback when dialog closes
    const handleOpenChange = (open: boolean) => {
        if (!open) {
            setFeedback({ type: null, message: '' });
            form.reset();
        }
        setIsOpen(open);
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleOpenChange}>
            <DialogTrigger asChild>
                <Button variant="outline" className="flex items-center gap-2">
                    <FaPlus size={16} />
                    <span>Import</span>
                </Button>
            </DialogTrigger>
            
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Import Document</DialogTitle>
                </DialogHeader>
                
                <Form {...form}>
                    <form className="space-y-4" onSubmit={form.handleSubmit(handleFileUpload)}>
                        <FormField
                            name="file"
                            control={form.control}
                            render={({ field: { value, onChange, ...fieldProps } }) => (
                                <FormItem>
                                    <FormLabel>Document</FormLabel>
                                    <FormControl>
                                        <Input 
                                            type="file" 
                                            accept=".pdf,.docx,.txt" 
                                            onChange={(e) => onChange(e.target.files)}
                                            disabled={isUploading}
                                            className="cursor-pointer"
                                            {...fieldProps}
                                        />
                                    </FormControl>
                                    <FormDescription>
                                        Upload a document (PDF, Word, or Text) to import into your space.
                                    </FormDescription>
                                </FormItem>
                            )}
                        />
                        
                        {/* Feedback alerts */}
                        {feedback.type === 'success' && (
                            <Alert variant="default" className="bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-900">
                                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                                <AlertTitle>Success</AlertTitle>
                                <AlertDescription>{feedback.message}</AlertDescription>
                            </Alert>
                        )}
                        
                        {feedback.type === 'error' && (
                            <Alert variant="destructive">
                                <AlertCircle className="h-4 w-4" />
                                <AlertTitle>Error</AlertTitle>
                                <AlertDescription>{feedback.message}</AlertDescription>
                            </Alert>
                        )}
                        
                        <DialogFooter className="sm:justify-start gap-2">
                            <Button 
                                type="submit" 
                                disabled={isUploading}
                            >
                                {isUploading ? "Uploading..." : "Upload"}
                            </Button>
                            <DialogClose asChild>
                                <Button type="button" variant="secondary">
                                    Cancel
                                </Button>
                            </DialogClose>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
