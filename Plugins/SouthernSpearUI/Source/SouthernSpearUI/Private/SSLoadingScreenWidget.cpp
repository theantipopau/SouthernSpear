// Copyright Southern Spear. All Rights Reserved.

#include "SSLoadingScreenWidget.h"

#include "Components/ScaleBox.h"
#include "Components/SizeBox.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "SSMenuWidget.h"
#include "SSOperations.h"
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
		NSLOCTEXT("SSLoading", "Tip5", "Press L to open role selection and choose a different role."),
	};

	void SetArt(UImage* Image, UTexture2D* Texture)
	{
		if (Image && Texture)
		{
			Image->SetBrushFromTexture(Texture, /*bMatchSize=*/ true);
		}
	}
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
	Art = T->ConstructWidget<UImage>();
	SetArt(Art, SSUIAssets::KeyArt());
	UScaleBox* Scale = T->ConstructWidget<UScaleBox>();
	Scale->SetStretch(EStretch::ScaleToFill);
	Scale->AddChild(Art);
	Fill(Root, Scale);

	// Bottom band: brass rule, then the operation and its rules on the left, LOADING on the right.
	UVerticalBox* Band = T->ConstructWidget<UVerticalBox>();
	UCanvasPanelSlot* BandSlot = Root->AddChildToCanvas(Band);
	BandSlot->SetAnchors(FAnchors(0.f, 1.f, 1.f, 1.f));
	BandSlot->SetAlignment(FVector2D(0.f, 1.f));
	BandSlot->SetOffsets(FMargin(0.f, 0.f, 0.f, 0.f));
	BandSlot->SetAutoSize(true);
	AddV(Band, Rule(T, SSPalette::Brass500(0.9f), 2.f));
	UBorder* BandPlate = Plate(T, SSPalette::Ink950(0.88f), FMargin(64.f, 22.f, 64.f, 26.f));
	AddV(Band, BandPlate);
	UHorizontalBox* Row = T->ConstructWidget<UHorizontalBox>();
	BandPlate->SetContent(Row);

	// The text column never runs wider than a comfortable reading line.
	USizeBox* Measure = T->ConstructWidget<USizeBox>();
	Measure->SetMaxDesiredWidth(980.f);
	AddH(Row, Measure, true, VAlign_Bottom);
	UVerticalBox* Left = T->ConstructWidget<UVerticalBox>();
	Measure->AddChild(Left);

	Kicker = Text(T, 11, true, SSPalette::Brass300(), 300);
	AddV(Left, Kicker);
	Title = Text(T, 34, true, SSPalette::Sand100(), 60);
	Title->SetText(NSLOCTEXT("SSLoading", "Title", "SOUTHERN SPEAR"));
	AddV(Left, Title, 2.f);
	Meta = Text(T, 11, true, SSPalette::Brass500(), 220);
	AddV(Left, Meta, 4.f);
	Description = Text(T, 14, false, SSPalette::Sage200());
	Description->SetAutoWrapText(true);
	AddV(Left, Description, 8.f);

	UVerticalBox* Mode = T->ConstructWidget<UVerticalBox>();
	ModeBlock = Mode;
	AddV(Left, Mode, 16.f);
	AddV(Mode, Rule(T, SSPalette::Brass500(0.35f), 1.f, 120.f), 0.f, HAlign_Left);
	ModeName = Text(T, 13, true, SSPalette::Sand100(), 200);
	AddV(Mode, ModeName, 12.f);
	ModeSummary = Text(T, 13, false, SSPalette::Sage200());
	ModeSummary->SetAutoWrapText(true);
	AddV(Mode, ModeSummary, 6.f);

	UTextBlock* Tip = Text(T, 12, false, SSPalette::Sage400());
	Tip->SetText(FText::Format(NSLOCTEXT("SSLoading", "TipLine", "TIP  ·  {0}"), Tips[FMath::RandRange(0, UE_ARRAY_COUNT(Tips) - 1)]));
	Tip->SetAutoWrapText(true);
	AddV(Left, Tip, 16.f);

	LoadingText = Text(T, 13, true, SSPalette::Brass300(), 300);
	LoadingText->SetText(NSLOCTEXT("SSLoading", "Loading", "LOADING"));
	AddH(Row, LoadingText, false, VAlign_Bottom)->SetPadding(FMargin(32.f, 0.f, 0.f, 0.f));

	// Until NativeConstruct knows the destination: the plain version.
	Kicker->SetVisibility(ESlateVisibility::Collapsed);
	Meta->SetVisibility(ESlateVisibility::Collapsed);
	Description->SetVisibility(ESlateVisibility::Collapsed);
	Mode->SetVisibility(ESlateVisibility::Collapsed);
	return true;
}

void USSLoadingScreenWidget::ResolveDestination(FString& OutMap, bool& bOutSection) const
{
	// The front end's request is the most reliable: it is set just before OpenLevel.
	OutMap = USSMenuWidget::PendingMap();
	bOutSection = USSMenuWidget::IsSectionRulesSelected();
	if (!OutMap.IsEmpty())
	{
		return;
	}
	// Otherwise (a map opened from the command line, a server travel): the engine's own travel URL.
	const UGameInstance* GameInstance = GetGameInstance();
	const FWorldContext* Context = GameInstance ? GameInstance->GetWorldContext() : nullptr;
	if (!Context)
	{
		return;
	}
	const FString Travel = Context->TravelURL.IsEmpty() ? Context->LastURL.ToString() : Context->TravelURL;
	FString Options;
	Travel.Split(TEXT("?"), &OutMap, &Options);
	if (OutMap.IsEmpty())
	{
		OutMap = Travel;
	}
	bOutSection = Travel.Contains(TEXT("Rules=Section"), ESearchCase::IgnoreCase);
}

void USSLoadingScreenWidget::NativeConstruct()
{
	Super::NativeConstruct();
	FString Map;
	bool bSection = false;
	ResolveDestination(Map, bSection);
	const SSOperations::FOperation* Op = SSOperations::Find(Map);
	if (!Op || !Title)
	{
		return; // the front end, or a map not in the list: the plain screen
	}
	SetArt(Art, SSUIAssets::OperationArt(Op->ArtKey));
	Kicker->SetText(NSLOCTEXT("SSLoading", "Kicker", "LOADING OPERATION"));
	Kicker->SetVisibility(ESlateVisibility::HitTestInvisible);
	Title->SetText(Op->Title.ToUpper());
	Meta->SetText(Op->Meta);
	Meta->SetVisibility(ESlateVisibility::HitTestInvisible);
	Description->SetText(Op->Description);
	Description->SetVisibility(ESlateVisibility::HitTestInvisible);
	const SSOperations::FMode Mode = SSOperations::Mode(bSection);
	ModeName->SetText(Mode.Name);
	ModeSummary->SetText(Mode.Summary);
	ModeBlock->SetVisibility(ESlateVisibility::HitTestInvisible);
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
