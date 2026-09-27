"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2 } from 'lucide-react';
import { vapiApi } from '@/lib/api-endpoints';
import { useToast } from '@/components/ui/use-toast';

export default function AssistantConfig() {
    const { toast } = useToast();
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);

    // Config state
    const [voice, setVoice] = useState('jennifer');
    const [instructions, setInstructions] = useState('');
    const [firstMessage, setFirstMessage] = useState('');
    const [assistantId, setAssistantId] = useState<string | null>(null);

    // KB State
    const [files, setFiles] = useState<any[]>([]);
    const [uploading, setUploading] = useState(false);

    // Tools State
    const [enableBooking, setEnableBooking] = useState(true);

    // Initial fetch
    useEffect(() => {
        async function loadConfig() {
            setFetching(true);
            try {
                const config = await vapiApi.getMyAssistant();
                if (config && config.assistant_id) {
                    setAssistantId(config.assistant_id);
                    setVoice(config.voice?.voiceId || config.voice || 'jennifer');
                    // Cleaner instruction extraction
                    const rawInst = config.model?.messages?.[0]?.content || config.instructions || '';
                    setInstructions(rawInst);
                    setFirstMessage(config.first_message || '');

                    // files
                    if (config.file_ids && config.file_ids.length > 0) {
                        // TODO: Map IDs to names if possible, for now just show count or fetch details
                        setFiles(config.file_ids.map((id: string) => ({ id, name: `File ${id.slice(0, 8)}...` })));
                    }
                }
            } catch (error) {
                console.error("Failed to load assistant config", error);
            } finally {
                setFetching(false);
            }
        }
        loadConfig();
    }, []);

    const handleSave = async () => {
        setLoading(true);
        try {
            const payload = {
                voice,
                instructions,
                first_message: firstMessage,
                file_ids: files.map(f => f.id),
                // Simple tool enable/disable based on bool
                // In real app, we'd construct the full tool definition or list of IDs
                // For now, we assume backend appends default tools or we send them here if we had the full tool definition
            };

            if (assistantId && assistantId !== 'loading') {
                await vapiApi.updateMyAssistant(payload);
                toast({
                    title: "Success",
                    description: "AI Assistant updated successfully",
                });
            } else {
                const result = await vapiApi.createMyAssistant(payload);
                setAssistantId(result.assistant_id);
                toast({
                    title: "Success",
                    description: "AI Assistant created successfully",
                });
            }
        } catch (error) {
            console.error("Failed to save assistant", error);
            toast({
                title: "Error",
                description: "Failed to save AI configuration",
                variant: "destructive"
            });
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.length) return;
        setUploading(true);
        try {
            const file = e.target.files[0];
            const result = await vapiApi.uploadFile(file);
            setFiles([...files, result]);
            toast({ title: "File uploaded", description: "Added to knowledge base." });
        } catch (err) {
            toast({ title: "Upload failed", description: "Could not upload file.", variant: "destructive" });
        } finally {
            setUploading(false);
        }
    };

    if (fetching) {
        return <div className="flex justify-center p-8"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div>;
    }

    return (
        <Card className="w-full max-w-3xl mx-auto">
            <CardHeader>
                <CardTitle>AI Receptionist Configuration</CardTitle>
                <CardDescription>Manage your voice agent's personality, knowledge, and capabilities.</CardDescription>
            </CardHeader>
            <CardContent>
                <Tabs defaultValue="general" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger value="general">General</TabsTrigger>
                        <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
                        <TabsTrigger value="tools">Tools & Actions</TabsTrigger>
                    </TabsList>

                    {/* GENERAL TAB */}
                    <TabsContent value="general" className="space-y-6 mt-4">
                        <div className="space-y-2">
                            <Label htmlFor="voice">Voice Personality</Label>
                            <Select value={voice} onValueChange={setVoice}>
                                <SelectTrigger id="voice">
                                    <SelectValue placeholder="Select a voice" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="jennifer">Jennifer (Professional & Polished)</SelectItem>
                                    <SelectItem value="sarah">Sarah (Warm & Friendly)</SelectItem>
                                    <SelectItem value="ryan">Ryan (Clear & Direct)</SelectItem>
                                    <SelectItem value="adam">Adam (Deep & Authoritative)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="first-message">First Message</Label>
                            <Input
                                id="first-message"
                                value={firstMessage}
                                onChange={(e) => setFirstMessage(e.target.value)}
                                placeholder="Hello! Thanks for calling [Business Name], how can I help you?"
                            />
                            <p className="text-sm text-gray-500">The first thing the AI says when the call is connected.</p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="instructions">System Instructions</Label>
                            <Textarea
                                id="instructions"
                                value={instructions}
                                onChange={(e) => setInstructions(e.target.value)}
                                placeholder="You are a helpful receptionist. You should help customers book appointments for haircuts..."
                                rows={8}
                            />
                        </div>
                    </TabsContent>

                    {/* KNOWLEDGE BASE TAB */}
                    <TabsContent value="knowledge" className="space-y-6 mt-4">
                        <div className="space-y-4">
                            <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center">
                                <p className="text-sm text-gray-500 mb-4">Upload PDFs, CSVs, or TXT files to train your assistant.</p>
                                <Label htmlFor="file-upload" className="cursor-pointer">
                                    <div className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex h-10 px-4 py-2 items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50">
                                        {uploading ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : null}
                                        Upload File
                                    </div>
                                    <Input id="file-upload" type="file" className="hidden" onChange={handleFileUpload} disabled={uploading} />
                                </Label>
                            </div>

                            <div className="space-y-2">
                                <h4 className="font-medium text-sm">Attached Files</h4>
                                {files.length === 0 && <p className="text-muted-foreground text-sm italic">No files attached.</p>}
                                <ul className="space-y-2">
                                    {files.map((file, i) => (
                                        <li key={i} className="flex items-center justify-between p-2 bg-muted rounded-md text-sm">
                                            <span>{file.name}</span>
                                            <Button variant="ghost" size="sm" onClick={() => {
                                                setFiles(files.filter(f => f.id !== file.id));
                                            }}>Remove</Button>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </TabsContent>

                    {/* TOOLS TAB */}
                    <TabsContent value="tools" className="space-y-6 mt-4">
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 border rounded-lg">
                                <div>
                                    <h4 className="font-medium">Appointment Booking</h4>
                                    <p className="text-sm text-gray-500">Allow the AI to check availability and book appointments.</p>
                                </div>
                                <div className="flex items-center space-x-2">
                                    {/* Simple switch simulation for now */}
                                    <Button
                                        variant={enableBooking ? "default" : "outline"}
                                        onClick={() => setEnableBooking(!enableBooking)}
                                    >
                                        {enableBooking ? "Enabled" : "Disabled"}
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </TabsContent>

                </Tabs>

                <div className="mt-8 pt-6 border-t">
                    <Button onClick={handleSave} disabled={loading} className="w-full md:w-auto md:float-right">
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {assistantId ? 'Save Changes' : 'Create Assistant'}
                    </Button>
                </div>

            </CardContent>
        </Card>
    );
}
