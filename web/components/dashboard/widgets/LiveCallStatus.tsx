import { Pause, Square } from "lucide-react";
import { Button } from "@/components/ui/button";

export const LiveCallStatus = () => {
    return (
        <div className="bg-gradient-to-br from-primary via-accent to-primary/90 rounded-2xl p-6 text-white relative overflow-hidden shadow-2xl shadow-primary/30 shine">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(255,255,255,0.15),rgba(255,255,255,0))]" />

            <div className="relative">
                <h3 className="text-lg font-semibold mb-2">Live Call Timer</h3>
                <p className="text-sm text-white/70 mb-6">Active support session</p>

                <div className="text-center mb-6">
                    <div className="text-5xl font-bold mb-2 font-mono">02:47:23</div>
                    <p className="text-sm text-white/70">Call in progress</p>
                </div>

                <div className="flex gap-3">
                    <Button
                        className="flex-1 bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/30"
                        size="lg"
                    >
                        <Pause className="w-5 h-5 mr-2" />
                        Pause
                    </Button>
                    <Button
                        className="flex-1 bg-destructive hover:bg-destructive/90"
                        size="lg"
                    >
                        <Square className="w-5 h-5 mr-2" />
                        End Call
                    </Button>
                </div>
            </div>
        </div>
    );
};
