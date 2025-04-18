"use client";

import { useEffect, useState } from "react";
import { useApp } from "@/context/app-context";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function AnalysisInterface() {
  const { setActiveNavTab } = useApp();
  const [analysisTab, setAnalysisTab] = useState("sentiment");

  // Set active tab to analysis when this page is loaded
  useEffect(() => {
    setActiveNavTab("analysis");
  }, [setActiveNavTab]);

  return (
    <div className="flex flex-col h-screen bg-background">
      <div className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-6">Phân tích bài đăng</h1>

        <Tabs
          value={analysisTab}
          onValueChange={setAnalysisTab}
          className="mb-6"
        >
          <TabsList>
            <TabsTrigger value="sentiment">Phân tích cảm xúc</TabsTrigger>
            <TabsTrigger value="topics">Phân tích chủ đề</TabsTrigger>
            <TabsTrigger value="reports">Báo cáo thống kê</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Sample content for analysis page */}
          <Card>
            <CardHeader>
              <CardTitle>Đánh giá cảm xúc</CardTitle>
              <CardDescription>
                Phân tích cảm xúc khách hàng trong tin nhắn
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[200px] bg-gray-100 rounded-md flex items-center justify-center">
                Biểu đồ cảm xúc
              </div>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">
                Xem chi tiết
              </Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Chủ đề thảo luận</CardTitle>
              <CardDescription>
                Các chủ đề phổ biến trong cuộc trò chuyện
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[200px] bg-gray-100 rounded-md flex items-center justify-center">
                Tag cloud
              </div>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">
                Xem chi tiết
              </Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Thời gian phản hồi</CardTitle>
              <CardDescription>
                Thống kê thời gian phản hồi tin nhắn
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[200px] bg-gray-100 rounded-md flex items-center justify-center">
                Biểu đồ thời gian
              </div>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">
                Xem chi tiết
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}
