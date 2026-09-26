// Copyright Southern Spear. All Rights Reserved.

#include "SSLoadingScreenWidget.h"

#include "Components/ScaleBox.h"
#include "SSUIAssets.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

namespace
{
	// Every tip must describe what the game actually does today.
	const FText Tips[] =
	{
		NSLOCTEXT("SSLoading", "Tip1", "Objectives fall in order. Take the active one to open the next."),
		NSLOCTEXT("SSLoading", "Tip2", "Stand inside an objective's ring to capture it. Opposing soldiers inside contest it."),
		NSLOCTEXT("SSLoading", "Tip3", "Press M for the full map. The minimap shows the objectives in your team's colours."),
		NSLOCTEXT("SSLoading", "Tip4", "Aim down sights with the right mouse button to steady your weapon."),
	};
}

bool USSLoadingScreenWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	Fill(Root, Plate(T, SSPalette::Ink950(), FMargin(0.f)));
	UImage* Art = T->ConstructWidget<UImage>();
	if (UTexture2D* Texture = SSUIAssets::KeyArt())
	{
		Art->SetBrushFromTexture(Texture, /*bMatchSize=*/ true);
	}
	UScaleBox* Scale = T->ConstructWidget<UScaleBox>();
	Scale->SetStretch(EStretch::ScaleToFill);
	Scale->AddChild(Art);
	Fill(Root, Scale);

	// Bottom band: brass rule, title, loading label, tip.
	UVerticalBox* Band = T->ConstructWidget<UVerticalBox>();
	UCanvasPanelSlot* BandSlot = Root->AddChildToCanvas(Band);
	BandSlot->SetAnchors(FAnchors(0.f, 1.f, 1.f, 1.f));
	BandSlot->SetAlignment(FVector2D(0.f, 1.f));
	BandSlot->SetOffsets(FMargin(0.f, 0.f, 0.f, 0.f));
	BandSlot->SetAutoSize(true);
	AddV(Band, Rule(T, SSPalette::Brass500(0.9f), 2.f));
	UBorder* Plate1 = Plate(T, SSPalette::Ink950(0.86f), FMargin(64.f, 18.f, 64.f, 22.f));
	AddV(Band, Plate1);
	UHorizontalBox* Row = T->ConstructWidget<UHorizontalBox>();
	Plate1->SetContent(Row);

	UVerticalBox* Left = T->ConstructWidget<UVerticalBox>();
	AddH(Row, Left, true);
	UTextBlock* Title = Text(T, 22, true, SSPalette::Sand100(), 160);
	Title->SetText(NSLOCTEXT("SSLoading", "Title", "SOUTHERN SPEAR"));
	AddV(Left, Title);
	UTextBlock* Tip = Text(T, 13, false, SSPalette::Sage200());
	Tip->SetText(Tips[FMath::RandRange(0, UE_ARRAY_COUNT(Tips) - 1)]);
	AddV(Left, Tip, 6.f);

	LoadingText = Text(T, 13, true, SSPalette::Brass300(), 300);
	LoadingText->SetText(NSLOCTEXT("SSLoading", "Loading", "LOADING"));
	AddH(Row, LoadingText, false, VAlign_Bottom);
	return true;
}

void USSLoadingScreenWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Elapsed += InDeltaTime;
	if (LoadingText)
	{
		const int32 Dots = static_cast<int32>(Elapsed * 2.f) % 4;
		LoadingText->SetText(FText::FromString(FString(TEXT("LOADING ")) + FString::ChrN(Dots, TEXT('.')) + FString::ChrN(3 - Dots, TEXT(' '))));
	}
}
